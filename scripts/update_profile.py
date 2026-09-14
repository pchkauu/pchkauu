#!/usr/bin/env python3
"""Build profile widgets from public GitHub data. Python 3.11+, standard library only."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


OWNER = "pchkauu"
ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    ("launch_mode", "EXECUTION"),
    ("package_context", "BOUNDARIES"),
    ("domain_error", "OUTCOMES"),
    ("observatory", "DIAGNOSTICS"),
    ("talker_bloc_effects", "DIAGNOSTICS"),
)
STABLE_TAG = re.compile(
    r"v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
THEMES = {
    "dark": {
        "background": "#0d1117", "panel": "#151c26", "border": "#303d4d",
        "text": "#edf4fc", "muted": "#a7b8cb", "blue": "#79b8ff",
        "teal": "#5ee3cb", "grid": "#1b2633",
        "chart": ("#79b8ff", "#5ee3cb", "#c4afff", "#ffc785", "#f5a5c8", "#a7b8cb"),
    },
    "light": {
        "background": "#f7faff", "panel": "#ffffff", "border": "#ccd8e6",
        "text": "#172d45", "muted": "#50647b", "blue": "#175eae",
        "teal": "#087969", "grid": "#e4ecf5",
        "chart": ("#175eae", "#087969", "#7652b7", "#a86113", "#af467d", "#64748b"),
    },
}


def get_json(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pchkauu-profile",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/{path}", headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub HTTP {error.code}: {path}") from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError(f"Could not read GitHub data: {path}") from None


def paginate(path):
    items = []
    separator = "&" if "?" in path else "?"
    page = 1
    while True:
        batch = get_json(f"{path}{separator}per_page=100&page={page}")
        if not isinstance(batch, list):
            raise RuntimeError(f"Expected a GitHub list: {path}")
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def eligible_repositories(repositories):
    return sorted(
        (
            repo for repo in repositories
            if repo.get("owner", {}).get("login", "").casefold() == OWNER.casefold()
            and repo.get("private") is False
            and repo.get("fork") is False
            and repo.get("archived") is False
            and repo["name"].casefold() != OWNER.casefold()
        ),
        key=lambda repo: repo["name"],
    )


def version_info(tags, releases):
    stable = []
    for tag in tags:
        name = tag["name"]
        if match := STABLE_TAG.fullmatch(name):
            stable.append((tuple(map(int, match.groups())), name))
    if not stable:
        return {"tag": None, "kind": None}
    tag = max(stable)[1]
    published = any(
        release["tag_name"] == tag
        and release.get("draft") is False
        and release.get("prerelease") is False
        and release.get("published_at")
        for release in releases
    )
    return {"tag": tag, "kind": "Release" if published else "Tag"}


def collect_profile():
    repositories = eligible_repositories(paginate(f"users/{OWNER}/repos?type=owner"))
    names = {repo["name"] for repo in repositories}
    versions = {}
    for name, _ in PACKAGES:
        if name not in names:
            raise RuntimeError(f"Featured repository is not public and active: {name}")
        path = f"repos/{OWNER}/{name}"
        versions[name] = version_info(paginate(f"{path}/tags"), paginate(f"{path}/releases"))

    languages = Counter()
    for repo in repositories:
        path = f"repos/{OWNER}/{quote(repo['name'], safe='')}/languages"
        counts = get_json(path)
        if not isinstance(counts, dict) or any(
            not isinstance(name, str) or type(size) is not int or size < 0
            for name, size in counts.items()
        ):
            raise RuntimeError(f"Invalid language byte counts: {path}")
        languages.update({name: size for name, size in counts.items() if size})
    return {
        "versions": versions,
        "languages": dict(languages),
        "repositories": len(repositories),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def text(x, y, value, color, size=24, anchor="start", mono=False, weight=400):
    family = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" if mono else (
        "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    )
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-family="{family}" font-weight="{weight}" text-anchor="{anchor}">'
        f'{escape(str(value))}</text>'
    )


def card(theme, number, title, subtitle, body, note, updated):
    colors = THEMES[theme]
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="520" '
        'viewBox="0 0 640 520" role="img" aria-labelledby="title description">'
        f'<title id="title">{escape(title)}</title>'
        f'<desc id="description">{escape(subtitle)} {escape(note)}. '
        f'Snapshot: {escape(updated)}.</desc>'
        '<defs><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0H0V32" fill="none" stroke="{colors["grid"]}" stroke-width="1"/>'
        '</pattern><clipPath id="bar"><rect x="32" y="174" width="576" height="30" '
        'rx="8"/></clipPath></defs>'
        f'<rect x="1" y="1" width="638" height="518" rx="20" '
        f'fill="{colors["background"]}" stroke="{colors["border"]}"/>'
        '<rect x="16" y="16" width="608" height="488" rx="12" fill="url(#grid)"/>'
        f'<path d="M32 24H88" stroke="{colors["teal"]}" stroke-width="3"/>'
        + text(32, 65, title, colors["text"], 32, weight=650)
        + text(32, 99, subtitle, colors["muted"], 22)
        + text(604, 63, number, colors["blue"], 22, anchor="end", mono=True)
        + body
        + f'<path d="M32 451H608" stroke="{colors["border"]}"/>'
        + text(32, 479, note, colors["muted"], 20)
        + text(32, 507, f"Snapshot · {updated}", colors["muted"], 18, mono=True)
        + '</svg>\n'
    )
    ET.fromstring(svg)
    return svg


def package_map(profile, theme):
    colors = THEMES[theme]
    body = f'<path d="M47 154V410" stroke="{colors["teal"]}" stroke-width="2"/>'
    for index, (name, role) in enumerate(PACKAGES):
        y = 128 + index * 64
        body += (
            f'<rect x="64" y="{y}" width="544" height="52" rx="8" '
            f'fill="{colors["panel"]}" stroke="{colors["border"]}"/>'
            f'<circle cx="47" cy="{y + 26}" r="6" '
            f'fill="{colors["background"]}" stroke="{colors["teal"]}" stroke-width="2"/>'
            + text(80, y + 34, name, colors["text"], 24, mono=True)
            + text(594, y + 33, role, colors["teal"], 18, anchor="end", weight=600)
        )
    return card(theme, "01", "Package map", "Five libraries. Four areas of responsibility.",
                body, "Grouped by purpose · not a dependency graph", profile["updated"])


def version_radar(profile, theme):
    colors = THEMES[theme]
    body = ""
    for index, (name, _) in enumerate(PACKAGES):
        y = 128 + index * 64
        info = profile["versions"][name]
        tag = info["tag"] or "No stable tag"
        visible = tag if len(tag) <= 13 else tag[:10] + "…"
        body += (
            text(32, y + 34, name, colors["text"], 24, mono=True)
            + f'<rect x="336" y="{y}" width="168" height="50" rx="9" '
            f'fill="{colors["panel"]}" stroke="{colors["border"]}"/>'
            + f'<g><title>{escape(tag)}</title>'
            + text(420, y + 33, visible, colors["blue"], 20, anchor="middle", mono=True)
            + '</g>'
            + text(608, y + 33, info["kind"] or "—", colors["teal"], 22, anchor="end")
        )
    return card(theme, "02", "Version radar", "Highest stable tag in each repository.",
                body, "Release = a matching published GitHub Release", profile["updated"])


def language_breakdown(languages):
    ordered = sorted(languages.items(), key=lambda item: (-item[1], item[0]))
    leading = ordered[:5]
    if len(ordered) > 5:
        leading.append(("Other", sum(size for _, size in ordered[5:])))
    return leading


def readable_bytes(size):
    for unit in ("B", "kB", "MB", "GB", "TB"):
        if size < 1000 or unit == "TB":
            return f"{size:,.0f} {unit}" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1000


def code_footprint(profile, theme):
    colors = THEMES[theme]
    languages = language_breakdown(profile["languages"])
    total = sum(profile["languages"].values())
    body = (
        text(32, 147, f'{profile["repositories"]} repositories', colors["text"], 26, weight=600)
        + text(608, 147, readable_bytes(total), colors["blue"], 26, anchor="end", mono=True)
    )
    if total:
        x = 32.0
        for index, (name, size) in enumerate(languages):
            width = size / total * 576
            color = colors["chart"][index]
            y = 241 + index * 36
            short_name = name if len(name) <= 24 else name[:21] + "…"
            body += (
                f'<rect x="{x:.3f}" y="174" width="{width:.3f}" height="30" '
                f'fill="{color}" clip-path="url(#bar)"/>'
                f'<circle cx="41" cy="{y - 8}" r="7" fill="{color}"/>'
                f'<g><title>{escape(name)}: {size} bytes</title>'
                + text(62, y, short_name, colors["text"], 24)
                + text(608, y, f"{size / total:.1%}", colors["text"], 24, anchor="end", mono=True)
                + '</g>'
            )
            x += width
    else:
        body += text(32, 259, "No public language data available.", colors["muted"], 26)
    return card(theme, "03", "Code footprint", "Public code, measured in bytes.", body,
                "Excludes forks, archives, and this profile", profile["updated"])


def render_widgets(profile):
    return {
        f"{name}-{theme}.svg": render(profile, theme)
        for name, render in (
            ("package-map", package_map),
            ("version-radar", version_radar),
            ("code-footprint", code_footprint),
        )
        for theme in THEMES
    }


def update(output_dir):
    # Read and validate the complete snapshot before replacing any files.
    widgets = render_widgets(collect_profile())
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, svg in widgets.items():
        (output_dir / name).write_text(svg, encoding="utf-8")
    return len(widgets)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets" / "widgets")
    args = parser.parse_args()
    try:
        count = update(args.output_dir)
    except (RuntimeError, OSError) as error:
        print(f"Profile update failed: {error}", file=sys.stderr)
        return 1
    print(f"Updated {count} widgets in {args.output_dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
