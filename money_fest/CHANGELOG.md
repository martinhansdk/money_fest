# Changelog

All notable changes to this add-on will be documented in this file.

## [1.0.7] - 2026-01-01

### Added
- Download button for all batch statuses (in-progress, complete, archived)
- CTRL+F (CMD+F on Mac) keyboard shortcut to focus payee filter in categorization view
- Support for YYYY/MM/DD and YYYY-MM-DD date formats in AceMoney CSV imports
- Support for AceMoney CSV header aliases: "Num" for "transaction", "S" for "status"

### Changed
- In-progress batches show confirmation dialog when downloading and are NOT auto-archived
- Complete batches continue to auto-archive after download
- CSV parser error messages now show both expected and found headers for easier troubleshooting
- CSV format guide updated with supported date formats and header aliases

## [1.0.6] - 2025-12-31

### Fixed
- Transaction display in categorization modal now shows properly styled amount (removed unrendered HTML)
- Amount text now displays in white for better readability on purple gradient background
- Filter input boxes now have consistent vertical alignment with proper heights
- Similar transactions dialog now uses searchable category input instead of dropdown
- Added inline category creation to similar transactions dialog (type "Parent:Child" format)

### Added
- Archive batch button for in-progress batches
- Archive batch confirmation dialog
- Batch archival functionality connected to existing backend endpoint

## [1.0.5] - 2025-12-31

### Added
- Category CRUD operations: create, update, and delete categories via API
- POST /categories endpoint to create new categories with auto-parent detection
- PUT /categories/{id} endpoint to update category name or hierarchy
- DELETE /categories/{id} endpoint to delete categories with required replacement
- Automatic cascade updates to child categories and transactions when renaming
- CategoryUpdate and CategoryDelete request models

### Changed
- Category updates now automatically update all child categories and related transactions
- Category deletion requires specifying a replacement category to maintain data integrity

## [1.0.4] - 2025-12-31

### Added
- Sortable transaction table columns (date, payee, amount, category)
- Transaction filters: payee (text search), amount (exact or range), category (text search)
- Click-to-copy amount functionality to quickly filter by exact amount
- Selected transaction display at top of categorization modal
- Clear filters button
- Visual sort indicators (▲ ▼) on table headers

### Changed
- Transaction table now supports multi-level filtering and sorting
- Amount cells are clickable for quick filtering

## [1.0.3] - 2025-12-31

### Added
- Batch deletion UI with confirmation dialog showing transaction count
- Delete button on each batch card in the batches list

## [1.0.2] - 2025-12-30

### Fixed
- Port mapping issue: App now correctly listens on port 8080 internally
- Container port mapping (8080:1111) now works as expected
- Users can now connect to the add-on on the configured external port

## [1.0.1] - 2025-12-30

### Fixed
- Add-on crash during SSL certificate generation
- Missing `openssl` package in Docker image
- Error handling in run.sh script when SSL generation fails
- Script now gracefully falls back to HTTP if SSL certificate generation fails

## [1.0.0] - 2025-12-30

### Added
- Initial Home Assistant add-on release
- Multi-architecture support (amd64, aarch64, armv7)
- Configurable port (default: 1111)
- Web-based first-time setup via /setup page
- Auto-import categories on first run (configurable)
- Comprehensive CLI tools for user management
- Support for AceMoney and Danske Bank CSV formats
- Real-time WebSocket synchronization between users
- Smart categorization with rules engine
- Similar transaction matching with fuzzy search
- Mobile-optimized UI
- Secure session-based authentication
- Database backup functionality

### Features from Base Application
- Session-based authentication with bcrypt password hashing
- 175+ pre-defined hierarchical expense categories
- Batch management (upload, categorize, download, archive)
- Transaction categorization with multi-select
- Category usage tracking and frequent categories
- Rule-based auto-categorization with suggestions
- CSV import/export (always AceMoney format output)
- WebSocket real-time collaboration
- Batch completion celebration with confetti
- Similar transaction detection (by payee, amount, date)
- Configurable similarity controls

### Configuration Options
- `port`: Network port for web interface (default: 1111)
- `secret_key`: Required secret key for session security
- `session_max_age`: Session duration in seconds (1-90 days)
- `log_level`: Logging verbosity (debug, info, warning, error)
- `auto_import_categories`: Auto-import categories on first run

### Documentation
- Comprehensive add-on documentation (DOCS.md)
- Add-on store description (README.md)
- CLI command reference
- Troubleshooting guide
- CSV format specifications
- Security notes

## [0.1.0] - Development

- Development of standalone Docker application (pre-add-on)
- Phases 1-6 completed:
  - Phase 1: Foundation (auth, database, CLI tools)
  - Phase 2: Core batch flow (CSV parsing, batch management)
  - Phase 3: Categorization (UI, transaction management)
  - Phase 4: Real-time sync (WebSocket, auto-reconnect)
  - Phase 5: Rules engine (suggestions, pattern matching)
  - Phase 6: Similar transactions (fuzzy matching, tolerance controls)
