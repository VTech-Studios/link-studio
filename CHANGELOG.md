# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- The preview is now a panel beside the settings instead of a tab of its
  own, so the picture stays in view while you adjust it. It still opens
  the camera only while switched on.
- Pages are chosen from a sidebar on the left rather than tabs along the
  top, and the settings and preview can be resized against each other.
- New dark theme with titled pages, grouped cards and line icons, applied
  the same way on every desktop.

## [1.0.0] - 2026-09-29

First release.

### Added

- Framing tab: pan, tilt and zoom sliders, a 5° nudge pad, centring, and six
  presets stored in the camera.
- Image tab: every standard V4L2 control the camera reports, built at
  runtime so new firmware controls appear without code changes.
- AI and modes tab: AI tracking on or off, tracking framing, and the Normal,
  DeskView, Whiteboard and Overhead modes, through `linkctl`.
- Preview tab that opens the camera only while switched on, so calls can
  keep using it.
- Rotated cam tab for the `cam-rotate` virtual camera, shown when
  `cam-rotate` is installed.
- Startup profiles, re-applied automatically whenever the camera connects
  through a systemd user service, with no root access needed.
- `link-studio --apply` for applying the saved profile without the GUI.

[Unreleased]: https://github.com/VTech-Studios/link-studio/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/VTech-Studios/link-studio/releases/tag/v1.0.0
