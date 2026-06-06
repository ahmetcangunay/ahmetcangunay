#!/usr/bin/env python3

import os
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
from urllib.error import URLError
from pathlib import Path

ERROR_PREVIEW_MAX_CHARS = 200
TROPHY_RANK_EXCLUSIONS = "-C,-B,-?"
REQUEST_TIMEOUT_SECONDS = 30


def build_url(username: str) -> str:
    params = urllib.parse.urlencode(
        {
            "username": username,
            "theme": "radical",
            "rank": TROPHY_RANK_EXCLUSIONS,
        }
    )
    return f"https://github-profile-trophy.vercel.app/?{params}"


def main() -> None:
    username = os.environ.get("GITHUB_USERNAME", "").strip()
    output_path = os.environ.get("TROPHY_OUTPUT", "profile/trophy.svg").strip()

    if not username:
        raise SystemExit("GITHUB_USERNAME environment variable is required but not set")
    relative_output = Path(output_path)
    if relative_output.is_absolute():
        raise SystemExit("TROPHY_OUTPUT must be a relative path")

    repo_root = Path.cwd().resolve()
    target = (repo_root / relative_output).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError:
        raise SystemExit("TROPHY_OUTPUT must stay within the repository directory")

    request = urllib.request.Request(
        build_url(username),
        headers={"User-Agent": "github-actions-generate-trophy"},
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise SystemExit(f"Failed to fetch trophy SVG: HTTP {response.status}")
            body = response.read()
            content_type = response.headers.get("Content-Type", "unknown")
    except URLError as exc:
        raise SystemExit(f"Failed to fetch trophy SVG: {exc}") from exc

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"Fetched content is not valid UTF-8: {exc}") from exc
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        root = None

    svg_tags = {"svg", "{http://www.w3.org/2000/svg}svg"}
    is_svg = root is not None and root.tag in svg_tags
    if not is_svg:
        preview = text[:ERROR_PREVIEW_MAX_CHARS].replace("\n", " ")
        raise SystemExit(
            f"Fetched content is not valid SVG "
            f"(content-type: {content_type}, preview: {preview!r})"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)


if __name__ == "__main__":
    main()
