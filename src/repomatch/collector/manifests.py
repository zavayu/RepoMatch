"""Recognize manifests and order them simply: roots, apps, then examples/docs."""

from pathlib import PurePosixPath

MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "Gemfile",
    "CMakeLists.txt",
    "Makefile",
    "mix.exs",
    "pubspec.yaml",
    "platformio.ini",
}
EXCLUDED_DIRECTORIES = {
    "node_modules", "vendor", ".git", ".venv", "venv", "dist",
    "build", "bin", "obj", "third_party", "third-party", "coverage",
}
SECONDARY_DIRECTORIES = {
    "docs", "doc", "documentation", "website",
    "examples", "example", "samples", "sample", "demos", "demo",
    "tests", "test", "testing", "fixtures", "__tests__",
}


def select_manifests(entries: list) -> list:
    """Keep project manifests; paths retain component information for later use."""
    candidates = []
    for entry in entries:
        if entry.get("type") != "file":
            continue
        name = entry["name"]
        if name not in MANIFEST_NAMES and not name.endswith((".csproj", ".fsproj")):
            continue
        directories = set(PurePosixPath(entry["path"]).parts[:-1])
        if not directories & EXCLUDED_DIRECTORIES:
            candidates.append(entry)

    def priority(entry):
        path = PurePosixPath(entry["path"])
        secondary = bool(set(path.parts[:-1]) & SECONDARY_DIRECTORIES)
        return secondary, len(path.parts), str(path)

    return sorted(candidates, key=priority)

