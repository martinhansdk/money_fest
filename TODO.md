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
- [x] Parse CSV with UTF-8 encoding (Danske Bank format)
- [x] Auto-detect CSV format (AceMoney vs Danske Bank)
- [x] Handle date format DD.MM.YYYY
- [x] Extract amount from withdrawal/deposit columns (AceMoney)
- [x] Extract amount from Beløb column with Danish decimals (Danske Bank)
- [x] Validate required fields
- [x] Return structured transaction data
- [x] Generate CSV output with categories (always AceMoney format)
- [x] Handle encoding issues gracefully

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

## Phase 4: Real-Time Sync

### WebSocket Backend
- [ ] WebSocket endpoint setup
- [ ] Connection manager (track connected clients)
- [ ] Subscribe to batch
- [ ] Broadcast transaction updates
- [ ] Broadcast batch progress
- [ ] Broadcast batch complete
- [ ] Handle disconnects gracefully

### WebSocket Frontend
- [ ] WebSocket connection on page load
- [ ] Auto-reconnect logic
- [ ] Subscribe when viewing batch
- [ ] Handle transaction_updated message
- [ ] Handle batch_progress message
- [ ] Handle batch_complete message
- [ ] Update UI without full refresh

### Celebration
- [ ] Detect batch completion (server-side)
- [ ] Send batch_complete event
- [ ] Frontend animation/toast
- [ ] CSS for celebration effect

---

## Phase 5: Rules Engine

### Rules Backend
- [ ] Rules table and model
- [ ] Create rule endpoint
- [ ] List rules endpoint
- [ ] Delete rule endpoint
- [ ] Match rules against transaction
- [ ] Get suggestions for transaction

### Rules UI
- [ ] "Create rule" button on transaction
- [ ] Rule creation modal:
  - [ ] Editable pattern field
  - [ ] Match type selector
  - [ ] Category pre-filled
- [ ] Rules management page
- [ ] Rule list with delete buttons

### Suggestions Display
- [ ] Match rules on batch load
- [ ] Display suggestions as chips on transactions
- [ ] One-tap to accept suggestion
- [ ] Handle multiple matching rules

---

## Phase 6: Similar Transactions

### Similar Backend
- [ ] Find similar by payee (fuzzy match)
- [ ] Find similar by amount (±10%)
- [ ] Get surrounding transactions (by date)
- [ ] Include transactions from all batches

### Similar UI
- [ ] "Show similar" button on transaction
- [ ] Similar transactions panel/modal
- [ ] Toggle: by payee / by amount
- [ ] Display with batch name, category
- [ ] Selectable for batch categorization
- [ ] "Show context" for surrounding transactions

---

## Phase 7: Polish

### UX Improvements
- [ ] Loading states for all async operations
- [ ] Error handling with user-friendly messages
- [ ] Toast notifications for actions
- [ ] Keyboard shortcuts (optional)
- [ ] Auto-advance to next uncategorized (optional)
- [ ] Remember sort/filter preferences

### Mobile Optimization
- [ ] Test on Android Chrome
- [ ] Touch target sizes (44px+)
- [ ] Viewport configuration
- [ ] Fast tap response (no 300ms delay)
- [ ] Pull-to-refresh on batch list

### Visual Polish
- [ ] Consistent color scheme
- [ ] Category color coding (optional)
- [ ] Amount formatting (red/green)
- [ ] Progress bar styling
- [ ] Celebration animation refinement

### Performance
- [ ] Pagination for large batches (if needed)
- [ ] Debounce search input
- [ ] Optimize database queries
- [ ] Minimize JS bundle size

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
