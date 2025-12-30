# Changelog

All notable changes to this add-on will be documented in this file.

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
