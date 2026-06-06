#!/usr/bin/env python3

import os
import urllib.parse
import urllib.request
from urllib.error import URLError
from pathlib import Path


def build_url(username: str) -> str:
    params = urllib.parse.urlencode(
        {
            "username": username,
            "theme": "radical",
            "rank": "-C,-B,-?",
        }
    )
    return f"https://github-profile-trophy.vercel.app/?{params}"


def main() -> None:
    username = os.environ.get("GITHUB_USERNAME", "").strip()
    output_path = os.environ.get("TROPHY_OUTPUT", "profile/trophy.svg").strip()

    if not username:
        raise SystemExit("GITHUB_USERNAME is required")

    request = urllib.request.Request(
        build_url(username),
        headers={"User-Agent": "github-actions-generate-trophy"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            content_type = response.headers.get("Content-Type", "unknown")
    except URLError as exc:
        raise SystemExit(f"Failed to fetch trophy SVG: {exc}") from exc

    text = body.decode("utf-8", errors="replace")
    if "<svg" not in text:
        preview = text[:200].replace("\n", " ")
        raise SystemExit(
            f"Fetched content is not valid SVG "
            f"(content-type: {content_type}, preview: {preview!r})"
        )

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)


if __name__ == "__main__":
    main()
