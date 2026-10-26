"""Look up the GitHub token without changing the process environment."""

import os
from pathlib import Path

from dotenv import dotenv_values


def get_github_token(root: Path) -> str:
    """Shell values override the project-local .env, including empty values."""
    if "GITHUB_TOKEN" in os.environ:
        token = os.environ["GITHUB_TOKEN"]
    else:
        values = dotenv_values(root / ".env", encoding="utf-8-sig", interpolate=False)
        token = values.get("GITHUB_TOKEN") or ""

    token = token.strip()
    return "" if token == "replace_with_your_token" else token

