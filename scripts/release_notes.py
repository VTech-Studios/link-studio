"""Release helpers used by the release workflow.

`python scripts/release_notes.py v1.0.0` prints that version's section of
CHANGELOG.md, which becomes the body of the GitHub release. With
`--check-tag` it instead fails unless the tag matches the package version,
so a mistyped tag can never publish files labelled with the wrong version.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION_FILE = ROOT / "link_studio" / "__init__.py"
_VERSION = re.compile(r'^__version__ = "(?P<version>[^"]+)"$', re.MULTILINE)


class ReleaseError(RuntimeError):
    """The repository is not in a releasable state."""


def version_from_tag(tag: str) -> str:
    """Strip the conventional `v` prefix from a tag such as `v1.0.0`."""
    return tag.removeprefix("v")


def package_version(source: str) -> str:
    """Read `__version__` from the package source without importing it.

    Importing would require the package's dependencies, which the release
    job does not install before building.
    """
    match = _VERSION.search(source)
    if match is None:
        raise ReleaseError("__version__ not found in link_studio/__init__.py")
    return match["version"]


def check_tag(tag: str, source: str) -> None:
    version = package_version(source)
    if version_from_tag(tag) != version:
        raise ReleaseError(f"Tag {tag} does not match the package version {version}")


def section(changelog: str, version: str) -> str:
    """Return the body of one version's changelog section.

    Sections follow Keep a Changelog: a `## [1.0.0] - date` heading, running
    until the next `## ` heading or the link references at the end.
    """
    heading = re.compile(rf"^## \[{re.escape(version)}\][^\n]*\n", re.MULTILINE)
    start = heading.search(changelog)
    if start is None:
        raise ReleaseError(f"CHANGELOG.md has no section for {version}")
    end = re.compile(r"^(## |\[[^\]]+\]: )", re.MULTILINE).search(changelog, start.end())
    body = changelog[start.end() : end.start() if end else len(changelog)].strip()
    if not body:
        raise ReleaseError(f"CHANGELOG.md section for {version} is empty")
    return body + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tag", help="release tag, for example v1.0.0")
    parser.add_argument("--check-tag", action="store_true", help="only check the tag against the version")
    args = parser.parse_args(argv)
    try:
        if args.check_tag:
            check_tag(args.tag, VERSION_FILE.read_text())
        else:
            sys.stdout.write(section(CHANGELOG.read_text(), version_from_tag(args.tag)))
    except ReleaseError as error:
        print(f"release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
