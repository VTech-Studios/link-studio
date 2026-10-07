# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
