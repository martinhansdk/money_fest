# Implementation TODO

## Phase 1: Foundation ✅ **COMPLETE**

### Project Setup ✅
- [x] Create project structure (see ARCHITECTURE.md)
- [x] Set up Docker and docker-compose
- [x] Create requirements.txt with dependencies
- [x] Configure FastAPI application
- [x] Set up SQLite database connection
- [x] Create database schema (all tables)
- [x] Create Pydantic models

### Authentication ✅
- [x] Implement password hashing (bcrypt)
- [x] Create users table and User model
- [x] Implement login endpoint
- [x] Implement logout endpoint
- [x] Session middleware with secure cookies
- [x] Auth dependency for protected routes
- [x] Login page HTML/CSS

### CLI Tools ✅
- [x] Create CLI module structure
- [x] `create-user` command (with --password, -it, and env var support)
- [x] `import-categories` command
- [x] `backup` command

**Phase 1 Status:** All 17 tasks complete. System tested and operational on port 1111.

---

## Phase 2: Core Batch Flow ✅ **COMPLETE**

### CSV Parser ✅
- [x] Parse CSV with latin-1 encoding (AceMoney format)
- [x] Parse CSV with UTF-8 and ISO-8859-1 encoding (Danske Bank format)
- [x] Auto-detect CSV format (AceMoney vs Danske Bank)
- [x] Handle date formats DD.MM.YYYY and DD-MM-YYYY
- [x] Extract amount from withdrawal/deposit columns (AceMoney)
- [x] Extract amount from Beløb column with Danish decimals (Danske Bank)
- [x] Validate required fields
- [x] Return structured transaction data
- [x] Generate CSV output with categories (always AceMoney format)
- [x] Handle encoding issues gracefully
- [x] Flexible encoding detection for real-world CSV files

### Batch Management ✅
- [x] Create batch endpoint (POST /batches)
- [x] List batches endpoint (GET /batches)
- [x] Get batch details endpoint (GET /batches/{id})
- [x] Delete batch endpoint (DELETE /batches/{id})
- [x] Download batch endpoint (GET /batches/{id}/download)
- [x] Auto-archive on download
- [x] Archive endpoint (POST /batches/{id}/archive)
- [x] Unarchive endpoint (POST /batches/{id}/unarchive)

### Batch API (Backend Complete) ✅
- [x] File upload handling (multipart/form-data)
- [x] Progress calculation (X/Y categorized, percentage)
- [x] Date range calculation from transactions
- [x] Status management (in_progress, archived)
- [x] Ownership verification
- [x] Batch filtering (include_archived parameter)
- [x] CSV download with auto-archive

**Phase 2 Backend Status:** All 21 backend tasks complete. Frontend UI (Phase 3) not yet started.

---

## Phase 3: Categorization ✅ **COMPLETE**

### Categories ✅
- [x] Import categories from file
- [x] Category model and table
- [x] List categories endpoint
- [x] Add category endpoint (not needed - categories pre-loaded)
- [x] Track usage counts
- [x] Frequent categories endpoint (top 15)

### Transaction CRUD ✅
- [x] List transactions for batch
- [x] Update transaction (category, note)
- [x] Bulk update transactions

### Categorization UI ✅
- [x] Batch list page (batches.html)
- [x] CSV upload modal with file picker
- [x] Transaction list table
- [x] Sortable columns (date, amount, payee) - native HTML table sorting
- [x] Filter tabs (All/Uncategorized/Categorized)
- [x] Row selection
- [x] Category selector component:
  - [x] Frequent categories buttons
  - [x] Search input with filtering
  - [x] Drill-down parent → child navigation (hierarchical display)
- [x] Note input field
- [x] Multi-select checkboxes
- [x] Bulk categorize action
- [x] Real-time progress tracking
- [x] Mobile-responsive design
- [x] Danish character encoding support (latin-1 and UTF-8)

**Phase 3 Status:** All 20 tasks complete. Full categorization UI implemented and tested.

---

## Phase 4: Real-Time Sync ✅ **COMPLETE**

### WebSocket Backend ✅
- [x] WebSocket endpoint setup
- [x] Connection manager (track connected clients)
- [x] Subscribe to batch
- [x] Broadcast transaction updates
- [x] Broadcast batch progress
- [x] Broadcast batch complete
- [x] Handle disconnects gracefully
- [x] Auto-reconnect with exponential backoff
- [x] Ping/pong keep-alive

### WebSocket Frontend ✅
- [x] WebSocket connection on page load
- [x] Auto-reconnect logic (exponential backoff, max 30s)
- [x] Subscribe when viewing batch
- [x] Handle transaction_updated message
- [x] Handle batch_progress message
- [x] Handle batch_complete message
- [x] Update UI without full refresh
- [x] Toast notifications for other users' updates

### Celebration ✅
- [x] Detect batch completion (server-side)
- [x] Send batch_complete event
- [x] Frontend confetti animation
- [x] CSS for celebration effect
- [x] Celebration toast message

**Phase 4 Status:** All 20 tasks complete. Real-time synchronization working with WebSocket.

---

## Phase 5: Rules Engine ✅ **COMPLETE**

### Rules Backend ✅
- [x] Rules table and model
- [x] Create rule endpoint
- [x] Update rule endpoint
- [x] List rules endpoint
- [x] Delete rule endpoint
- [x] Match rules against transaction (suggestions-only, not auto-apply)
- [x] Get suggestions for transaction endpoint
- [x] Preview transactions matching a rule pattern

### Rules UI ✅
- [x] "Create rule from transaction" prompt after categorization
- [x] Rules management page (rules.html)
- [x] Rule creation/editing with:
  - [x] Editable pattern field
  - [x] Match type selector (contains/exact)
  - [x] Category selector
  - [x] Live preview of matching transactions
  - [x] Debounced preview updates
- [x] Rule list with edit/delete buttons
- [x] Navigation to rules page from batches

### Suggestions Display ✅
- [x] Load rule suggestions when categorizing
- [x] Display suggestions as gold-colored chips
- [x] Show which rule created the suggestion
- [x] One-tap to accept suggestion
- [x] Handle multiple matching rules (all shown as suggestions)

**Phase 5 Status:** All 18 tasks complete. Rules engine with suggestion-based workflow implemented.

---

## Phase 6: Similar Transactions ✅ **COMPLETE**

### Similar Backend ✅
- [x] Find similar by payee (fuzzy match)
- [x] Find similar by amount (±10%)
- [x] Get surrounding transactions (by date)
- [x] Include transactions from all batches
- [x] Configurable similarity threshold (API parameter)
- [x] Configurable amount tolerance (API parameter)
- [x] Fix negative amount tolerance bug

### Similar UI ✅
- [x] "Show similar" button on transaction
- [x] Similar transactions panel/modal
- [x] Toggle: by payee / by amount / by date
- [x] Display with batch name, category
- [x] Selectable for batch categorization
- [x] "Show context" for surrounding transactions
- [x] Reference transaction display at top of modal
- [x] Similarity slider (0-100%) for payee matching
- [x] Amount tolerance slider (0-50%) for amount matching
- [x] Context-aware slider visibility (per tab)

**Phase 6 Status:** All 17 tasks complete. Similar transactions feature with configurable fuzzy matching, tolerance controls, and bulk categorization implemented.

---

## Phase 7: Polish ⏳ **PARTIALLY COMPLETE**

### UX Improvements ✅
- [x] Loading states for all async operations
- [x] Error handling with user-friendly messages
- [x] Toast notifications for actions
- [x] Debounced search in category selector
- [x] Debounced preview in rules management
- [ ] Keyboard shortcuts (optional, deferred)
- [ ] Auto-advance to next uncategorized (optional, deferred)
- [ ] Remember sort/filter preferences (deferred)

### Mobile Optimization ⏳
- [ ] Test on Android Chrome (not tested yet)
- [x] Touch target sizes (44px+)
- [x] Viewport configuration
- [x] Fast tap response (no 300ms delay)
- [ ] Pull-to-refresh on batch list (deferred)

### Visual Polish ✅
- [x] Consistent color scheme (purple gradient)
- [x] Amount formatting (red/green)
- [x] Progress bar styling
- [x] Celebration confetti animation
- [x] Gold-styled rule suggestions
- [ ] Category color coding (optional, deferred)

### Performance ✅
- [x] Debounce search input (300ms)
- [x] Debounce rule preview (500ms)
- [ ] Pagination for large batches (not needed yet)
- [ ] Optimize database queries (deferred)
- [ ] Minimize JS bundle size (deferred)

---

## Phase 8: Deployment

### Docker
- [ ] Finalize Dockerfile
- [ ] Health check endpoint
- [ ] Volume for database persistence
- [ ] Environment variable configuration

### Documentation
- [ ] README with setup instructions
- [ ] Configuration options
- [ ] Backup/restore procedure
- [ ] Troubleshooting guide

### Testing
- [ ] Run full test suite
- [ ] Manual end-to-end testing
- [ ] Test on actual phones
- [ ] Test concurrent usage

---

## Deferred / Maybe Later
- [ ] Dark mode
- [ ] Category colors
- [ ] Import/export rules
- [ ] Statistics page (spending by category)
- [ ] Date range filter on batch list
- [ ] Search across all batches
- [ ] Undo last categorization
