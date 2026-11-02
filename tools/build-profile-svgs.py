#!/usr/bin/env python3
"""Build the profile panels in assets/ and assets/dark/.

Every panel is 1000 units wide. Light and dark are separate files so the
palette is baked in; the README pairs them with <picture><source>.

    python tools/build-profile-svgs.py

The generator checks its own output: no text may cross the 48..952 margin and
no two labels may collide. A non-zero exit means the layout needs work.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CONTRIB = ROOT / "tools" / "contributions.json"

LEFT, RIGHT, WIDTH = 48, 952, 1000
MONO = 'ui-monospace,"SFMono-Regular","SF Mono",Menlo,Consolas,"Liberation Mono",monospace'

THEMES = {
    "light": {
        "bone": "#121b22",
        "muted": "#4b5864",
        "dim": "#5d6975",
        "rule": "#dde3e8",
        "accent": "#0f766e",
        "ghost": "#eef1f4",
        "track": "#eef1f4",
        "l1": "#d7ebe8",
        "l2": "#9ed3cc",
        "l3": "#4bb2a7",
    },
    "dark": {
        "bone": "#e8eff4",
        "muted": "#a3b0bb",
        "dim": "#7f8d99",
        "rule": "#26313a",
        "accent": "#2dd4bf",
        "ghost": "#171f27",
        "track": "#1a232b",
        "l1": "#173330",
        "l2": "#1e4d47",
        "l3": "#2a7d73",
    },
}

CSS = """
.mono{{font-family:{mono}}}
.draw{{stroke-dasharray:1400;stroke-dashoffset:1400;animation:draw 1.5s cubic-bezier(.6,0,.2,1) .1s forwards}}
.fade{{opacity:0;animation:fade .7s ease .1s forwards}}
.rise{{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) forwards}}
.grow{{transform:scaleX(0);animation:grow 1s cubic-bezier(.2,.7,.2,1) forwards}}
.pulse{{animation:pulse 2.6s ease-in-out infinite}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes grow{{to{{transform:scaleX(1)}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
.a1{{animation-delay:.15s}}.a2{{animation-delay:.3s}}.a3{{animation-delay:.45s}}.a4{{animation-delay:.6s}}
.a5{{animation-delay:.75s}}.a6{{animation-delay:.9s}}.a7{{animation-delay:1.05s}}.a8{{animation-delay:1.2s}}
@media (prefers-reduced-motion:reduce){{
  .draw{{stroke-dashoffset:0;animation:none}}
  .fade,.rise{{opacity:1;animation:none}}
  .grow{{transform:none;animation:none}}
  .pulse{{animation:none}}
}}
""".format(mono=MONO)

FONTS = [
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/Cour.ttf",
]


def num(value: float) -> str:
    return f"{value:g}"


class Panel:
    def __init__(self, name: str, height: int, theme: dict, aria: str):
        self.name = name
        self.height = height
        self.p = theme
        self.aria = aria
        self.parts: list[str] = []
        self.texts: list[tuple[str, float, float, float, float, str]] = []

    # -- primitives -----------------------------------------------------
    def raw(self, markup: str) -> None:
        self.parts.append(markup)

    def text(
        self,
        x: float,
        y: float,
        value: str,
        size: float = 13,
        fill: str = "bone",
        ls: float = 0,
        anchor: str = "start",
        weight: int | None = None,
        cls: str | None = None,
        opacity: float | None = None,
    ) -> None:
        attrs = [f'x="{num(x)}"', f'y="{num(y)}"', f'font-size="{num(size)}"']
        attrs.append(f'fill="{self.p[fill]}"')
        if ls:
            attrs.append(f'letter-spacing="{num(ls)}"')
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if opacity is not None:
            attrs.append(f'opacity="{num(opacity)}"')
        self.parts.append(f'<text {" ".join(attrs)}>{html.escape(value)}</text>')
        self.texts.append((value, x, y, size, ls, anchor))

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = "rule",
        width: float = 1,
        opacity: float | None = 1,
        cls: str | None = None,
        dash: str | None = None,
    ) -> None:
        attrs = [
            f'x1="{num(x1)}"',
            f'y1="{num(y1)}"',
            f'x2="{num(x2)}"',
            f'y2="{num(y2)}"',
            f'stroke="{self.p[stroke]}"',
            f'stroke-width="{num(width)}"',
        ]
        if opacity is not None and opacity != 1:
            attrs.append(f'opacity="{num(opacity)}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        self.parts.append(f'<line {" ".join(attrs)}/>')

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "ghost",
        stroke: str | None = None,
        radius: float = 0,
        cls: str | None = None,
        style: str | None = None,
        opacity: float | None = None,
    ) -> None:
        attrs = [
            f'x="{num(x)}"',
            f'y="{num(y)}"',
            f'width="{num(w)}"',
            f'height="{num(h)}"',
            f'fill="{self.p[fill]}"',
        ]
        if stroke:
            attrs.append(f'stroke="{self.p[stroke]}"')
        if radius:
            attrs.append(f'rx="{num(radius)}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        if opacity is not None:
            attrs.append(f'opacity="{num(opacity)}"')
        self.parts.append(f'<rect {" ".join(attrs)}/>')

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str = "accent",
        stroke: str | None = None,
        cls: str | None = None,
        style: str | None = None,
    ) -> None:
        attrs = [
            f'cx="{num(cx)}"',
            f'cy="{num(cy)}"',
            f'r="{num(r)}"',
            f'fill="{self.p[fill] if fill != "none" else "none"}"',
        ]
        if stroke:
            attrs.append(f'stroke="{self.p[stroke]}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if style:
            attrs.append(f'style="{style}"')
        self.parts.append(f'<circle {" ".join(attrs)}/>')

    # -- header ---------------------------------------------------------
    def figure_header(self, label: str, fig: str) -> None:
        self.line(LEFT, 40, RIGHT, 40)
        self.text(LEFT, 28, label, 11, "muted", ls=3.5)
        self.text(RIGHT, 28, fig, 11, "muted", ls=3.5, anchor="end")

    # -- output ---------------------------------------------------------
    def build(self) -> str:
        body = "\n  ".join(self.parts)
        return (
            f'<svg viewBox="0 0 {WIDTH} {self.height}" fill="none" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{html.escape(self.aria, quote=True)}">\n'
            f"  <style>{CSS}</style>\n"
            f'  <g class="mono">\n  {body}\n  </g>\n</svg>\n'
        )

    def check(self) -> list[str]:
        problems: list[str] = []
        spans = []
        for value, x, y, size, ls, anchor in self.texts:
            width = len(value) * size * 0.57 + max(0, len(value) - 1) * ls
            if anchor == "start":
                lo, hi = x, x + width
            elif anchor == "end":
                lo, hi = x - width, x
            else:
                lo, hi = x - width / 2, x + width / 2
            spans.append((lo, hi, y, value))
            if hi > RIGHT + 2:
                problems.append(f"right overflow {hi:.0f} :: {value[:52]}")
            if lo < LEFT - 2 and size < 40:
                problems.append(f"left overflow {lo:.0f} :: {value[:52]}")
        for i, (lo1, hi1, y1, v1) in enumerate(spans):
            for lo2, hi2, y2, v2 in spans[i + 1 :]:
                if abs(y1 - y2) < 3 and lo1 < hi2 - 6 and lo2 < hi1 - 6:
                    problems.append(f"collision {v1[:26]!r} / {v2[:26]!r}")
        return problems


# ---------------------------------------------------------------- header
def build_header(theme: dict) -> Panel:
    p = Panel("header", 400, theme, "Atilio Obadia — open source systems developer, Tanzania")
    p.line(LEFT, 58, RIGHT, 58, cls="draw")
    p.text(LEFT, 44, "PORTFOLIO — INDEX Nº 001", 11, "muted", ls=3.5, cls="fade a1")
    p.text(
        RIGHT, 44, "EAST AFRICA COMMUNITY · TANZANIA", 11, "muted", ls=3.5,
        anchor="end", cls="fade a1",
    )
    p.text(LEFT - 2, 176, "Atilio Obadia", 72, "bone", cls="rise a2")
    p.text(
        LEFT, 214,
        "Open source systems developer — ERPNext, Frappe, integrations.",
        19, "muted", cls="fade a3",
    )
    p.text(LEFT, 274, "focus  ▸", 12.5, "dim", ls=1, cls="fade a4")
    p.text(
        128, 274,
        "ERPNext · Frappe · custom systems · integrations · infrastructure",
        12.5, "accent", ls=1, cls="fade a4",
    )
    p.text(
        LEFT, 300, "accepting projects · open to collaboration",
        12.5, "dim", ls=1, cls="fade a5",
    )
    p.line(LEFT, 342, RIGHT, 342, cls="draw a5")
    p.text(LEFT, 374, "ERPNEXT & FRAPPE", 11.5, "muted", ls=3, cls="fade a6")
    p.text(248, 374, "·", 11.5, "accent", cls="fade a6")
    p.text(282, 374, "CUSTOM SYSTEMS", 11.5, "muted", ls=3, cls="fade a6")
    p.text(542, 374, "·", 11.5, "accent", cls="fade a6")
    p.text(576, 374, "INTEGRATIONS", 11.5, "muted", ls=3, cls="fade a6")
    p.text(RIGHT, 374, "ERPCODEC", 11.5, "muted", ls=3, anchor="end", cls="fade a6")
    return p


# -------------------------------------------------------------- sections
SECTIONS = [
    ("01", "WHOAMI", "~/01-whoami"),
    ("02", "SYSTEM MAP", "~/02-system-map"),
    ("03", "PROJECTS", "~/03-projects"),
    ("04", "TELEMETRY", "~/04-telemetry"),
    ("05", "THE ROUTE", "~/05-the-route"),
    ("06", "STACK", "~/06-stack"),
]


def build_section(theme: dict, index: str, label: str, path: str) -> Panel:
    p = Panel(f"s{index}", 92, theme, f"Section {index} — {label}")
    p.text(LEFT, 68, index, 52, "ghost")
    p.text(128, 58, label, 14, "accent", ls=6, cls="fade a1")
    p.text(RIGHT, 58, path, 11, "muted", ls=2, anchor="end", cls="fade a1")
    start = 128 + len(label) * 14 * 0.6 + max(0, len(label) - 1) * 6 + 26
    p.line(start, 53, min(RIGHT - 130, 840), 53, cls="draw a1")
    return p


# ---------------------------------------------------------------- whoami
def build_whoami(theme: dict) -> Panel:
    p = Panel("whoami", 236, theme, "About Atilio Obadia — ERPNext, Frappe, Tanzania")
    p.text(LEFT, 32, "Systems developer in Tanzania — ERPNext, Frappe and the systems around them.",
           15, "bone", cls="rise a1")
    p.text(LEFT, 60, "Implementation, localisation, integrations, and the infrastructure that keeps them running.",
           15, "bone", cls="rise a2")
    p.text(LEFT, 88, "Started in IT support and networks. Ended up in ERP, where every system answers for its ledger.",
           15, "muted", cls="rise a3")
    p.line(LEFT, 116, RIGHT, 116, opacity=0.7, cls="rise a4")
    rows = [
        ("FOCUS", "ERPNext & Frappe · localisation · integrations · infrastructure", "bone", "a4"),
        ("STATUS", "accepting projects · open to collaboration", "accent", "a5"),
        ("BRAND", "ERPcodec — systems development under Savari Limited", "bone", "a6"),
    ]
    for i, (label, value, fill, cls) in enumerate(rows):
        y = 148 + i * 34
        p.text(LEFT, y, label, 11, "muted", ls=2.5, cls=f"rise {cls}")
        p.text(154, y, value, 15, fill, cls=f"rise {cls}")
    return p


# ------------------------------------------------------------- ecosystem
NODES = [
    (75, 138, "ERPNext rollouts", "chart of accounts · go-live"),
    (48, 268, "CSF Tanzania", "v16 localisation · statutory"),
    (85, 388, "production ledger", "multi-branch · TBBCL"),
    (300, 76, "AIMSCAMS", "SACCO back office · ledger"),
    (545, 83, "warehouse mgmt", "items · stock · locations"),
    (755, 158, "client portals", "private builds · ongoing"),
    (760, 293, "payroll dashboard", "components · runs · payslips"),
    (270, 438, "BDS Tanzania", "corporate site · systems"),
    (630, 393, "DICOHAS College", "institutional website"),
    (100, 540, "ClickPesa", "payments · REST APIs"),
    (410, 540, "biometric sync", "attendance → ERPNext"),
    (720, 540, "pgautopilot", "postgres MCP server"),
]


def build_ecosystem(theme: dict) -> Panel:
    p = Panel("ecosystem", 680, theme,
              "System map: ERPNext and Frappe work, custom systems, integrations, infrastructure")
    p.figure_header("SYSTEM MAP — EVERYTHING FROM ONE PIPELINE", "FIG. 01")
    p.line(LEFT, 646, RIGHT, 646)
    p.text(RIGHT, 668, "DASHED LINES — DATA IN MOTION", 10, "dim", ls=2, anchor="end")

    core = (405, 252, 190, 56)
    cutouts = [
        f'<rect x="{core[0] - 2}" y="{core[1] - 2}" width="{core[2] + 4}" height="{core[3] + 4}" fill="black"/>'
    ]
    for x, y, _, _ in NODES:
        cutouts.append(f'<rect x="{x - 2}" y="{y - 2}" width="184" height="58" fill="black"/>')
    p.raw(
        '<defs><mask id="node-cutouts" maskUnits="userSpaceOnUse" '
        f'x="0" y="0" width="1000" height="680">'
        f'<rect x="0" y="0" width="1000" height="680" fill="white"/>'
        + "".join(cutouts)
        + "</mask></defs>"
    )

    cx, cy = core[0] + core[2] / 2, core[1] + core[3] / 2
    wires = []
    flows = []
    for x, y, _, _ in NODES:
        nx, ny = x + 90, y + 27
        wires.append(f'<line class="draw" x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}"/>')
        flows.append(
            f'<line x1="{cx}" y1="{cy}" x2="{nx}" y2="{ny}" stroke="{theme["muted"]}" '
            f'stroke-width="1" opacity=".22" stroke-dasharray="3 9"/>'
        )
    p.raw('<g mask="url(#node-cutouts)">' + "".join(wires) + "</g>")
    p.raw('<g mask="url(#node-cutouts)">' + "".join(flows) + "</g>")

    clusters = [
        (165, 118, "ERP & FRAPPE"),
        (512, 60, "CUSTOM SYSTEMS"),
        (845, 142, "PRODUCTS · PORTALS"),
        (500, 622, "INTEGRATIONS · AI · INFRASTRUCTURE"),
    ]
    for x, y, label in clusters:
        p.text(x, y, label, 10, "accent", ls=3, anchor="middle", cls="fade a3")

    p.raw('<g class="rise a1">')
    p.raw(
        f'<rect x="{core[0]}" y="{core[1]}" width="{core[2]}" height="{core[3]}" '
        f'rx="2" fill="none" stroke="{theme["rule"]}"/>'
    )
    p.parts.append("</g>")
    p.text(cx, 276, "ERPCODEC.SYS", 13, "bone", ls=2, anchor="middle", cls="fade a2")
    p.text(cx, 294, "one-person build pipeline", 8.5, "muted", ls=0.5, anchor="middle", cls="fade a2")

    for i, (x, y, title, sub) in enumerate(NODES):
        cls = f"fade a{min(8, 1 + i // 2)}"
        p.raw(f'<g class="{cls}">')
        p.raw(
            f'<rect x="{x}" y="{y}" width="180" height="54" rx="2" '
            f'fill="none" stroke="{theme["rule"]}"/>'
        )
        p.parts.append("</g>")
        p.text(x + 90, y + 23, title, 12, "bone", ls=1, anchor="middle")
        p.text(x + 90, y + 42, sub, 9, "muted", ls=1, anchor="middle")
    return p


# -------------------------------------------------------------- projects
PROJECTS = [
    (
        "AIMSCAMS",
        "Back office for Tanzanian SACCOs and microfinance institutions, built on a double-entry ledger.",
        "Members and KYC, savings and shares, credit, teller operations and regulatory returns.",
        "TYPESCRIPT · NEXT.JS · NESTJS · POSTGRESQL",
    ),
    (
        "CSF TANZANIA V16",
        "Tanzania localisation for Frappe and ERPNext v16 — the country layer, kept outside core.",
        "Statutory returns, tax handling, country chart of accounts and the numbering regulators expect.",
        "PYTHON · FRAPPE · ERPNEXT V16",
    ),
    (
        "WAREHOUSE MANAGEMENT",
        "Warehouse system for X Electronics: items, stock movements, locations and the records behind them.",
        "Every movement leaves a traceable entry, so counts stop living in notebooks.",
        "PYTHON · FRAPPE",
    ),
    (
        "ERPNEXT PAYROLL DASHBOARD",
        "Payroll workspace for ERPNext: salary components, payroll runs and settlement in one view.",
        "Built to sit on the desk, not beside it — the numbers come from the records payroll posts.",
        "PYTHON · FRAPPE · ERPNEXT",
    ),
    (
        "AIMS AI AGENT",
        "LLM assistant for the AIMS ecosystem, embedded where the records live, not in a separate tab.",
        "Tooling exposed through MCP, so a question about a member or a journal is answered in place.",
        "TYPESCRIPT · MCP · LLM TOOLING",
    ),
    (
        "FRAPPE CUSTOM COLOR",
        "White-label desk theming for Frappe and ERPNext v16 with zero edits to core.",
        "A client's brand on the interface their staff are trained on, and it survives the next upgrade.",
        "CSS · FRAPPE · DESK THEMING",
    ),
    (
        "ERPNEXT PRINT FORMATS",
        "Print formats for ERPNext documents — invoices, receipts and statements as the business files them.",
        "Jinja templates kept in version control instead of living in a database field.",
        "HTML · PYTHON · JINJA",
    ),
    (
        "ALPHA-ERPNEXT-FIXTURES",
        "Reusable fixture data so a new ERPNext site starts consistent instead of hand-built each time.",
        "Company, accounts, tax templates and masters, exported once and replayed.",
        "PYTHON · FRAPPE · FIXTURES",
    ),
    (
        "BDS TANZANIA",
        "Corporate website and internal business system for the Business Development Society of Tanzania.",
        "Public presence and the working records behind it, from one codebase.",
        "HTML · CSS · JAVASCRIPT",
    ),
    (
        "PGAUTOPILOT",
        "PostgreSQL MCP server that lets an AI assistant query and administer a database safely.",
        "Schema-aware generation behind read and write controls, published on npm.",
        "TYPESCRIPT · MCP · POSTGRESQL",
    ),
]


def build_projects(theme: dict) -> Panel:
    height = 20 + len(PROJECTS) * 110
    p = Panel("projects", height, theme, f"{len(PROJECTS)} selected projects by Atilio Obadia")
    for i, (title, line1, line2, meta) in enumerate(PROJECTS):
        top = 20 + i * 110
        p.text(LEFT, top + 24, f"{i + 1:02d} / {title}", 17, "bone", weight=700, ls=0.8,
               cls="fade a1")
        p.text(LEFT, top + 49, line1, 12, "muted")
        p.text(LEFT, top + 68, line2, 12, "muted")
        p.text(LEFT, top + 87, meta, 11, "dim", ls=0.4)
        p.line(LEFT, top + 104, RIGHT, top + 104)
    return p


# ------------------------------------------------------------- telemetry
LANGS = [("python", 11, 39), ("typescript", 5, 18), ("html", 5, 18),
         ("css", 3, 11), ("php", 2, 7), ("other", 2, 7)]
MONTHS = [("MAY", 6), ("JUN", 1), ("JUL", 7), ("AUG", 14), ("SEP", 1), ("OCT", 3)]


def build_telemetry(theme: dict) -> Panel:
    p = Panel("telemetry", 330, theme,
              "Telemetry: language distribution, repositories by month, profile counters")
    p.figure_header("TELEMETRY — WHAT THE HANDS ARE DOING", "FIG. 02")
    p.line(360, 64, 360, 296, opacity=0.45)
    p.line(688, 64, 688, 296, opacity=0.45)

    p.text(LEFT, 78, "LANGUAGES · FIRST-PARTY REPOS", 10, "dim", ls=2.5)
    for i, (label, count, pct) in enumerate(LANGS):
        y = 108 + i * 38
        width = 230 * count / 11
        fill = "accent" if i == 0 else "bone"
        p.text(LEFT, y, label, 11, "bone")
        p.rect(LEFT, y + 8, 230, 6, fill="track")
        p.rect(LEFT, y + 8, width, 6, fill=fill, cls=f"grow a{i + 1}",
               style=f"transform-origin:{num(LEFT)}px 0")
        p.text(LEFT + width + 10, y + 15, f"{pct}%", 10, "muted")

    p.text(392, 78, "REPOSITORIES BY MONTH · 2026", 10, "dim", ls=2.5)
    base, peak = 252, 120
    p.line(392, base, 656, base)
    for i, (label, value) in enumerate(MONTHS):
        x = 392 + i * 44
        h = peak * value / 14
        fill = "accent" if value == 14 else "bone"
        p.rect(x, base - h, 24, h, fill=fill, cls=f"grow a{i + 2}",
               style=f"transform-origin:{num(x)}px {num(base)}px")
        p.text(x + 12, base - h - 8, str(value), 10, "muted", anchor="middle")
        p.text(x + 12, 272, label, 9.5, "dim", ls=1, anchor="middle")
    p.text(392, 300, "busiest month — august, 14 new repositories", 10, "muted", ls=1.5)

    counters = [
        ("50", "REPOSITORIES", "bone"),
        ("10", "PROJECTS DOCUMENTED", "bone"),
        ("6", "CLIENT ENGAGEMENTS", "bone"),
        ("4", "CAPABILITY AREAS", "accent"),
    ]
    for i, (value, label, fill) in enumerate(counters):
        y = 118 + i * 58
        p.text(720, y, value, 44, fill, cls=f"rise a{min(8, i + 4)}")
        p.text(790, y - 6, label, 10, "muted", ls=2.5, cls=f"rise a{min(8, i + 4)}")
    return p


# ----------------------------------------------------------------- stats
def build_stats(theme: dict) -> Panel:
    p = Panel("stats", 310, theme, "GitHub statistics and repository languages")
    p.rect(24, 20, 456, 270, fill="ghost", stroke="rule", radius=2)
    p.rect(520, 20, 456, 270, fill="ghost", stroke="rule", radius=2)

    p.text(52, 58, "GITHUB — AT A GLANCE", 15, "bone", weight=700, ls=2)
    p.line(52, 72, 452, 72)
    rows = [
        ("PUBLIC REPOSITORIES", "50"),
        ("STARS ACROSS REPOS", "9"),
        ("FOLLOWERS", "15"),
        ("FORKED REPOS", "18"),
        ("MEMBER SINCE", "2025"),
    ]
    for i, (label, value) in enumerate(rows):
        y = 110 + i * 36
        p.text(52, y, label, 11, "muted", ls=1)
        p.text(436, y, value, 13, "bone", anchor="end")

    p.text(548, 58, "LANGUAGES BY REPOSITORY", 15, "bone", weight=700, ls=2)
    p.line(548, 72, 948, 72)
    bars = [("PYTHON", 11, 270), ("TYPESCRIPT", 5, 123), ("HTML", 5, 123),
            ("CSS", 3, 74), ("PHP", 2, 49), ("OTHER", 2, 49)]
    for i, (label, _, width) in enumerate(bars):
        y = 105 + i * 36
        p.text(548, y, label, 10, "muted")
        p.rect(660, y - 9, 270, 12, fill="track", stroke="rule")
        p.rect(660, y - 9, width, 12, fill="accent" if i == 0 else "bone",
               cls=f"grow a{i + 1}", style="transform-origin:660px 0")
    return p


# -------------------------------------------------------------- activity
def load_contrib() -> dict:
    if not CONTRIB.exists():
        raise SystemExit(
            f"missing {CONTRIB.name}; run tools/fetch_contributions.py first"
        )
    return json.loads(CONTRIB.read_text(encoding="utf-8"))


def build_activity(theme: dict) -> Panel:
    data = load_contrib()
    weeks = data["weeks"]
    p = Panel("activity", 240, theme,
              f"Contribution heatmap: {data['total']} contributions in the last year")

    p.line(LEFT, 34, RIGHT, 34)
    p.text(LEFT, 22, "CONTRIBUTION TELEMETRY — LAST 12 MONTHS", 11, "muted", ls=3.5)
    p.text(RIGHT, 22, "FIG. 03", 11, "muted", ls=3.5, anchor="end")

    p.text(LEFT, 112, f"{data['total']:,}", 46, "bone")
    p.text(LEFT, 134, "CONTRIBUTIONS IN THE LAST YEAR", 10, "muted", ls=2)
    p.text(LEFT, 166, f"{data['active_days']} active days", 11, "bone")
    p.text(LEFT, 186, f"{data['longest_streak']} day longest streak", 11, "muted")
    p.text(LEFT, 206, f"peak {data['peak_day']} on {data['peak_date']}", 10, "dim", ls=0.5)

    grid_x, grid_y, step, cell = 296, 96, 12, 9
    months = ["jan", "feb", "mar", "apr", "may", "jun",
              "jul", "aug", "sep", "oct", "nov", "dec"]
    last_label = -99
    for w, week in enumerate(weeks):
        for row, entry in enumerate(week):
            level = entry["l"]
            fill = ["track", "l1", "l2", "l3", "accent"][level]
            p.rect(grid_x + w * step, grid_y + row * step, cell, cell, fill=fill, radius=1.5)
        date = week[0]["d"]
        month = int(date[5:7]) - 1
        if w - last_label >= 4 and date[8:] <= "07":
            p.text(grid_x + w * step, 86, months[month], 9, "dim", ls=1)
            last_label = w

    legend_y = 198
    p.text(816, legend_y, "less", 9, "dim", ls=1, anchor="end")
    for i in range(5):
        p.rect(828 + i * 11, legend_y - 8, 8, 8,
               fill=["track", "l1", "l2", "l3", "accent"][i], radius=1.5)
    p.text(892, legend_y, "more", 9, "dim", ls=1)
    return p


# -------------------------------------------------------------- timeline
MILESTONES = [
    (130, "2023", "Gisee site — contributor", "up"),
    (278, "2024", "tourism site · DICOHAS College", "down"),
    (426, "2025", "BDS Tanzania — site & system", "up"),
    (574, "2026", "ERPNext v16 localisation", "down"),
    (722, "2026", "AIMSCAMS back office", "up"),
    (870, "NOW", "ERPcodec · open to work", "down"),
]


def build_timeline(theme: dict) -> Panel:
    p = Panel("timeline", 250, theme, "Timeline: 2023 to now")
    p.figure_header("THE ROUTE SO FAR", "FIG. 04")
    p.line(LEFT, 125, 952, 125, cls="draw")
    for i, (x, year, label, side) in enumerate(MILESTONES):
        cls = f"fade a{min(8, i + 1)}"
        if side == "up":
            p.line(x, 121, x, 96)
            p.text(x, 74, year, 11, "accent", ls=2, anchor="middle", cls=cls)
            p.text(x, 90, label, 10.5, "bone", ls=1, anchor="middle")
        else:
            p.line(x, 129, x, 154)
            p.text(x, 172, year, 11, "accent", ls=2, anchor="middle", cls=cls)
            p.text(x, 188, label, 10.5, "bone", ls=1, anchor="middle")
        if year == "NOW":
            p.circle(x, 125, 5, fill="none", stroke="accent", cls="pulse")
            p.circle(x, 125, 4, fill="accent")
        else:
            p.circle(x, 125, 4, fill="bone")
    p.text(952, 222, "2026 → the interesting part", 11, "dim", ls=1.5, anchor="end")
    return p


# ------------------------------------------------------------ experience
ROLES = [
    ("NOW", "ERPcodec · founder · Savari Limited · Tanzania", [
        "ERPNext implementation, custom systems, integrations and infrastructure for East African organisations",
        "six engagements on record — TBBCL, AATL, PMM, Mtokoma, BDS Tanzania, DICOHAS College",
    ]),
    ("2026", "AIMSCAMS · SACCO and microfinance back office", [
        "members and KYC, savings and shares, credit and teller operations on one double-entry ledger",
        "built for Tanzanian SACCOs, where the books are the business",
    ]),
    ("2025–26", "Tanzania localisation · CSF_TZ for Frappe and ERPNext v16", [
        "statutory returns, tax handling and country chart of accounts, kept out of core",
        "extended into desk theming, print formats and fixtures for repeatable site builds",
    ]),
    ("2023–25", "IT support and networks · biometrics, servers, DNS, hosting", [
        "the unglamorous layer — machines, LANs, backups and monitoring — that decides whether Monday works",
        "moved from fixing hardware into building the systems that replaced the paper",
    ]),
]


def build_experience(theme: dict) -> Panel:
    p = Panel("experience", 370, theme, "Practice: ERPNext, localisation, custom systems, infrastructure")
    p.line(120, 10, 120, 360, opacity=0.45)
    for i, (year, title, lines) in enumerate(ROLES):
        top = 42 + i * 96
        cls = f"rise a{min(8, i + 1)}"
        p.text(LEFT, top, year, 12, "accent", ls=2, cls=cls)
        p.text(136, top, title, 15, "bone", cls=cls)
        p.text(136, top + 26, lines[0], 14, "muted")
        p.text(136, top + 48, lines[1], 14, "muted")
    return p


# ----------------------------------------------------------------- stack
STACK = [
    ("LANGUAGES", "TypeScript · Python · JavaScript · PHP · HTML / CSS · SQL"),
    ("ERP", "ERPNext v16 · Frappe Framework · bench CLI · server scripts · custom apps"),
    ("WEB", "Next.js · React · NestJS · Tailwind · REST APIs"),
    ("DATA", "PostgreSQL · Frappe ORM · schema design · query tuning · migrations"),
    ("AI", "MCP servers · LLM agents · RAG · OpenAI-compatible APIs"),
    ("INFRA", "Linux · Nginx · Docker · DNS and hosting · backups and monitoring"),
    ("TOOLING", "Git · GitHub Actions · bench · Postman · VS Code · cPanel / WHM"),
]


def build_stack(theme: dict) -> Panel:
    p = Panel("stack", 250, theme, "Stack: languages, ERP, web, data, AI, infrastructure, tooling")
    p.line(138, 8, 138, 238, opacity=0.45)
    for i, (label, value) in enumerate(STACK):
        y = 32 + i * 32
        cls = f"rise a{min(8, i + 1)}"
        p.text(LEFT, y, label, 12, "muted", ls=2, cls=cls)
        p.text(154, y, value, 15, "bone", cls=cls)
    return p


# ---------------------------------------------------------------- footer
def build_footer(theme: dict) -> Panel:
    p = Panel("footer", 110, theme, "Status: accepting projects · Tanzania")
    p.line(LEFT, 24, RIGHT, 24, cls="draw")
    p.circle(60, 64, 6, fill="none", stroke="accent", cls="pulse")
    p.circle(60, 64, 4, fill="accent")
    p.text(82, 62, "STATUS — ACCEPTING PROJECTS", 12, "bone", ls=3)
    p.text(82, 82, "ERPNext · Frappe · integrations — East Africa Community, Tanzania",
           11, "muted", ls=2)
    p.text(RIGHT, 66, "atilioobadia-cpu.github.io/profile_personel · © 2026",
           13, "muted", anchor="end")
    return p


# ------------------------------------------------------------------ main
def main() -> int:
    (ASSETS / "dark").mkdir(parents=True, exist_ok=True)
    panels: list[Panel] = []
    for theme_name, theme in THEMES.items():
        built = [
            build_header(theme),
            *[build_section(theme, *row) for row in SECTIONS],
            build_whoami(theme),
            build_ecosystem(theme),
            build_projects(theme),
            build_telemetry(theme),
            build_stats(theme),
            build_activity(theme),
            build_timeline(theme),
            build_experience(theme),
            build_stack(theme),
            build_footer(theme),
        ]
        target = ASSETS / theme_name if theme_name == "dark" else ASSETS
        target.mkdir(parents=True, exist_ok=True)
        for panel in built:
            (target / f"{panel.name}.svg").write_text(panel.build(), encoding="utf-8")
        panels.extend(built)
        print(f"{theme_name}: {len(built)} panels -> {target}")

    problems = []
    for panel in panels:
        for problem in panel.check():
            problems.append(f"{panel.name}: {problem}")

    if problems:
        print(f"\n{len(problems)} layout problem(s):")
        for problem in problems[:40]:
            print("  " + problem)
        return 1

    print(f"\nlayout: 0 overflow, 0 collisions across {len(panels)} panels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
