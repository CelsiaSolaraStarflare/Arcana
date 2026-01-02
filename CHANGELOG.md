# Changelog

All notable changes for this development session are recorded here.

## [Unreleased] - 2026-01-01

### Added
- Kai DBMS: hybrid search pipeline with Kai-Instant (fast) and Kai-Think (reranked) modes, optional semantic embeddings, and adaptive fusion.
- Settings: DBMS mode selector (Fiber/Kai) and a test query panel for comparing search behavior.

## [Unreleased] - 2025-06-26

### Added
- Major Finder (File Manager) overhaul:
  - Card-based UI for files and folders with clear action buttons.
  - Create, rename, move, and delete operations for both files and folders.
  - Uploads now go to the currently viewed directory.
  - Reminder message prompting users to re-index after file operations.
- `settings.py` log display overhaul:
  - Single scrollable code block (`st.code`) for the full changelog.
  - Removed redundant separate "Recent AI Code Fixes" section (merged into this changelog).
- Robust DB reload logic after indexing using the existing `dbms` instance.
- **CHANGELOG.md** to keep a persistent record of updates.
- Grammar Refiner workspace wired into the main navigation and documented in the README.
- Settings toggles for enabling Rewrite Refiner diagnostics and AI quality checks.

### Changed
- `finder.py`:
  - Switched to `shutil.move` for cross-filesystem moves.
  - Refactored display logic into `_display_item` helper.
  - Added delete and rename utilities and cleaner layout.
- `settings.py`:
  - Displays the changelog once per session; prevents duplicate rendering.
- `indexing.py`: safer `.pptx` text extraction and clearer logging.
- `mixup.py`: improved placeholder handling, typing, and error suppression.
- `chatbot.py`: added sidebar file uploader; prioritises uploaded files in responses.
- `editor.py`, `response.py`, `longresponse.py`: fixed streaming and typing issues for a smoother user experience.
- `Arcanalte.py`: modernised sidebar navigation with a collapsible advanced-tools section and Grammar Refiner hook-up.
- `README.md`: expanded navigation guide with Rewrite Refiner workflows.

### Removed
- Legacy radio-button navigation logic from `Arcanalte.py`.
