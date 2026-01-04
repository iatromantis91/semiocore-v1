# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]

## [1.0.1] - 2026-01-01
### Added
- Normative v1 contract documents for `semiocore.trace.v1` and `semiocore.ctxscan.v1`.
- Cross-platform CI matrix (Ubuntu/Windows/macOS) for Python 3.11–3.13.

### Changed
- CI installs test dependencies via `pyproject.toml` extras (declarative install).

### Fixed
- Cross-platform conformance hashing stability (path normalization / stable views) for trace/ctxscan artifacts.

## [1.0.0] - 2025-12-30
- Initial stable release.
