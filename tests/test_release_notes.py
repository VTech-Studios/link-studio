import pytest

from scripts.release_notes import (
    CHANGELOG,
    VERSION_FILE,
    ReleaseError,
    check_tag,
    main,
    package_version,
    section,
    version_from_tag,
)

CHANGELOG_TEXT = """# Changelog

## [Unreleased]

## [1.1.0] - 2026-10-01

### Fixed

- Something.

## [1.0.0] - 2026-09-29

First release.

[Unreleased]: https://example.com/compare/v1.1.0...HEAD
[1.1.0]: https://example.com/releases/tag/v1.1.0
"""


def test_version_from_tag() -> None:
    assert version_from_tag("v1.0.0") == "1.0.0"
    assert version_from_tag("1.0.0") == "1.0.0"


def test_package_version() -> None:
    assert package_version('"""Doc."""\n\n__version__ = "1.2.3"\n') == "1.2.3"


def test_package_version_missing() -> None:
    with pytest.raises(ReleaseError, match="not found"):
        package_version("nothing here")


def test_check_tag_accepts_a_match_and_rejects_a_mismatch() -> None:
    source = '__version__ = "1.0.0"\n'

    check_tag("v1.0.0", source)
    with pytest.raises(ReleaseError, match=r"v1\.0\.1 does not match the package version 1\.0\.0"):
        check_tag("v1.0.1", source)


def test_section_stops_at_the_next_heading() -> None:
    assert section(CHANGELOG_TEXT, "1.1.0") == "### Fixed\n\n- Something.\n"


def test_last_section_stops_at_the_link_references() -> None:
    assert section(CHANGELOG_TEXT, "1.0.0") == "First release.\n"


def test_missing_and_empty_sections_are_errors() -> None:
    with pytest.raises(ReleaseError, match=r"no section for 9\.9\.9"):
        section(CHANGELOG_TEXT, "9.9.9")
    with pytest.raises(ReleaseError, match="Unreleased is empty"):
        section(CHANGELOG_TEXT, "Unreleased")


def test_repository_is_releasable_as_versioned() -> None:
    version = package_version(VERSION_FILE.read_text())

    check_tag(f"v{version}", VERSION_FILE.read_text())
    assert section(CHANGELOG.read_text(), version).startswith("First release.")


def test_main_prints_notes(capsys: pytest.CaptureFixture[str]) -> None:
    version = package_version(VERSION_FILE.read_text())

    assert main([f"v{version}"]) == 0
    assert "First release." in capsys.readouterr().out


def test_main_rejects_a_wrong_tag(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["v0.0.0", "--check-tag"]) == 1
    assert "does not match" in capsys.readouterr().err
