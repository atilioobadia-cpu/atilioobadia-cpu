#!/usr/bin/env python3
"""Snapshot the public contribution calendar for the profile activity panel.

GitHub serves the calendar as plain HTML at /users/<name>/contributions, so no
token is needed. The snapshot is written to tools/contributions.json and read by
tools/build-profile-svgs.py.

    python tools/fetch_contributions.py
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import date
from pathlib import Path

USER = "atilioobadia-cpu"
OUT = Path(__file__).resolve().parent / "contributions.json"

CELL = re.compile(
    r"<td\b([^>]*)>.*?</td>\s*<tool-tip[^>]*>(.*?)</tool-tip>",
    re.S,
)
ATTR = {
    "date": re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"'),
    "level": re.compile(r'data-level="(\d)"'),
    "cell": re.compile(r'id="contribution-day-component-(\d+)-(\d+)"'),
}


def fetch() -> str:
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def count_of(tooltip: str) -> int:
    found = re.search(r"([\d,]+)\s+contribution", tooltip)
    return int(found.group(1).replace(",", "")) if found else 0


def parse(page: str) -> dict:
    weeks: list[list[dict]] = []
    starts = [m.start() for m in re.finditer(r"<td\b", page)]
    starts.append(len(page))
    for index in range(len(starts) - 1):
        block = page[starts[index] : starts[index + 1]]
        head = block[: block.find(">") + 1]
        cell = ATTR["cell"].search(head)
        day = ATTR["date"].search(head)
        level = ATTR["level"].search(head)
        if not (cell and day and level):
            continue
        tooltip = re.search(r"<tool-tip[^>]*>(.*?)</tool-tip>", block, re.S)
        row, week = int(cell.group(1)), int(cell.group(2))
        while len(weeks) <= week:
            weeks.append([])
        weeks[week].append(
            {
                "d": day.group(1),
                "l": int(level.group(1)),
                "c": count_of(tooltip.group(1) if tooltip else ""),
                "r": row,
            }
        )

    for week in weeks:
        week.sort(key=lambda cell: cell["r"])

    flat = [cell for week in weeks for cell in week]
    best = 0
    run = 0
    for cell in flat:
        run = run + 1 if cell["c"] else 0
        best = max(best, run)

    return {
        "user": USER,
        "generated": date.today().isoformat(),
        "weeks": [
            [{"d": c["d"], "l": c["l"], "c": c["c"]} for c in week] for week in weeks
        ],
        "total": sum(cell["c"] for cell in flat),
        "active_days": sum(1 for cell in flat if cell["c"]),
        "longest_streak": best,
        "peak_day": max(cell["c"] for cell in flat),
        "peak_date": max(flat, key=lambda cell: cell["c"])["d"],
    }


def main() -> None:
    data = parse(fetch())
    OUT.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    print(
        f"{data['user']}: {data['total']} contributions, "
        f"{data['active_days']} active days, "
        f"{len(data['weeks'])} weeks -> {OUT.name}"
    )


if __name__ == "__main__":
    main()
