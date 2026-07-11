# AGENTS.md

This is a package for Sublime Text.

## Repository Shape

- `main.py` is the package entrypoint.
  It clears cached `PackageDev.plugins.*` modules before re-importing `plugins`.
- `plugins/` holds all Sublime runtime code.
  New plugin classes must be imported from `plugins/__init__.py` or they will be missed.
- `Package/` holds shipped Sublime resource files and syntax definitions.

## Commands

- Lint Python with `uv run ruff check .`.
- Ruff is configured for `line-length = 99` and selects `E`, `F`, `I`, and `UP`.
- There is no repo Python test suite.
  Use Sublime Text as the primary runtime check.

## Syntax Tests

- CI runs syntax tests for changed `*.sublime-syntax`, `syntax_test*`, and `.tmPreferences` files.
- The matrix covers stable, latest, and build `4136`, plus a tolerated latest/master run.

## Editing Rules

- Preserve the current plugin import surface in `plugins/__init__.py`.
- Keep Python 3.8+ compatibility in mind.
- Treat `PackageDev.sublime-project` and `*.sublime-workspace` as local files; they are ignored.
- When changing YAML serialization or built-in metadata, verify behavior in Sublime, not with unit tests.
