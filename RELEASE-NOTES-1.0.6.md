# Release Notes - Version 1.0.6

**Release Date:** January 1, 2026

## Summary

This release fixes 4 user-reported UI issues and restructures the repository for faster development iteration.

## UI Fixes

### 1. Transaction Display Styling
**Issue:** Transaction display in categorization modal showed unrendered HTML (`<span>` tags) and red text was hard to read on dark blue gradient.

**Fix:**
- Removed HTML-generating `formatAmount()` function call
- Display amount as plain white text on purple gradient background
- Format: "Netto | Dec 1, 2024 | -42.50"

**Impact:** Clean, readable transaction display with proper visual hierarchy

### 2. Filter Input Alignment
**Issue:** Filter input boxes had uneven vertical alignment.

**Fix:**
- Added consistent heights to all filter components:
  - Labels: 18px
  - Input fields: 38px with `box-sizing: border-box`
  - Helper text: 14px
  - Clear Filters button: 38px with `align-self: flex-end`
- Added `flex: 1; min-width: 150px` for even distribution

**Impact:** Professional, aligned filter section

### 3. Similar Transactions Category Search
**Issue:** Category selection used a dropdown that was difficult to navigate with many categories.

**Fix:**
- Replaced `<select>` dropdown with searchable text input
- Added autocomplete that filters categories as you type
- Implemented inline category creation (type "Food:NewItem" to create)
- Auto-fills reference transaction's category if present

**Impact:** Much faster category selection and ability to create categories on the fly

### 4. Archive Batch UI
**Issue:** No UI to archive a batch.

**Fix:**
- Added Archive button (shows only for `in_progress` batches)
- Implemented confirmation dialog
- Connected to existing `POST /batches/{id}/archive` endpoint
- Success notification after archiving

**Impact:** Users can now archive batches from the UI

## Category CRUD Operations

Added full Create, Read, Update, Delete functionality for categories via API:

### New Endpoints

**POST /categories**
- Create categories with "Parent:Child" notation
- Automatic parent detection and validation
- Prevents duplicates

**PUT /categories/{id}**
- Update category name or change parent
- Automatically cascades to all child categories
- Updates all transactions using the category

**DELETE /categories/{id}**
- Requires replacement category ID
- Safely migrates all transactions to replacement
- Deletes category and all children
- Updates usage counts

### Backend Changes

**Files Modified:**
- `money_fest/app/models.py` - Added CategoryCreate, CategoryUpdate, CategoryDelete
- `money_fest/app/routers/categories.py` - Added CRUD endpoints
- `money_fest/app/services/category.py` - Implemented CRUD logic with cascade updates

## Development Workflow Improvements

### Repository Restructuring

**Problem:** Application code was duplicated in both `/app/` and `/money_fest/app/`, requiring manual syncing and slow rebuilds.

**Solution:** Established single source of truth with volume mounts for fast iteration.

### Changes

1. **Single Source:** `money_fest/app/` is now the canonical application code
2. **Removed Duplicates:** Deleted `/app/`, `/tests/`, and `/categories.txt` from root
3. **Volume Mounts:** Development environment mounts files instead of copying:
   ```yaml
   volumes:
     - ./money_fest/app:/app/app
     - ./money_fest/categories.txt:/app/categories.txt
   ```

### Development Speed

**Before:**
- Edit file → Build Docker image (2-3 minutes) → Restart → Test

**After:**
- Edit HTML/CSS/JS → Refresh browser (~5 seconds)
- Edit Python → `docker compose restart` (~10 seconds)
- Only rebuild for `requirements.txt` or Dockerfile changes

### Documentation

Created `DEV-SETUP.md` with:
- Directory structure explanation
- Quick start guide
- Development workflow documentation
- Common tasks reference

## Files Changed

### Add-on Files (v1.0.6)
- `money_fest/CHANGELOG.md` - Updated with release notes
- `money_fest/config.yaml` - Version bumped to 1.0.6
- `money_fest/app/static/categorize.html` - UI fixes
- `money_fest/app/static/batches.html` - Archive button
- `money_fest/app/models.py` - Category CRUD models
- `money_fest/app/routers/categories.py` - CRUD endpoints
- `money_fest/app/services/category.py` - CRUD implementations

### Development Infrastructure
- `Dockerfile` - Updated to copy from `money_fest/`
- `docker-compose.yml` - Added volume mounts
- `DEV-SETUP.md` - New development guide
- `.gitignore` - Added Playwright test artifacts

### Deleted (Duplicates)
- `/app/` directory (all files)
- `/tests/` directory (all files)
- `/categories.txt`

## Testing

All fixes were tested using Playwright browser automation:
- ✅ Transaction display shows correctly with white text
- ✅ Filter inputs are properly aligned
- ✅ Archive button works with confirmation
- ✅ Similar transactions category search (verified structure, full testing pending)

## Git Commits

1. `5e4a0ca` - Release version 1.0.6 with UI fixes and category CRUD
2. `cdf6895` - Restructure repository for faster development workflow
3. `5b4f7c0` - Add Playwright test artifacts to gitignore

## Upgrade Notes

For developers:
1. Pull latest changes: `git pull`
2. Rebuild container: `docker compose down && docker compose build && docker compose up -d`
3. All future edits go in `money_fest/app/` directory
4. No rebuild needed for most changes!

For Home Assistant users:
- Update add-on to version 1.0.6 through the add-on store
- No breaking changes, database migrations not required

## Known Issues

None reported.

## Contributors

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
