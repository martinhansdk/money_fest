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

## Phase 2: Core Batch Flow

### CSV Parser
- [ ] Parse CSV with latin-1 encoding
- [ ] Handle date format DD.MM.YYYY
- [ ] Extract amount from withdrawal/deposit columns
- [ ] Validate required fields
- [ ] Return structured transaction data
- [ ] Generate CSV output with categories

### Batch Management
- [ ] Create batch endpoint (POST /batches)
- [ ] List batches endpoint (GET /batches)
- [ ] Get batch details endpoint (GET /batches/{id})
- [ ] Delete batch endpoint (DELETE /batches/{id})
- [ ] Download batch endpoint (GET /batches/{id}/download)
- [ ] Auto-archive on download
- [ ] Unarchive endpoint (POST /batches/{id}/unarchive)

### Batch UI
- [ ] Batch list page
- [ ] Upload form with name input
- [ ] Progress display (X/Y, percentage bar)
- [ ] Date range display
- [ ] Status indicators
- [ ] Archive filter toggle
- [ ] Delete confirmation dialog
- [ ] Download button

---

## Phase 3: Categorization

### Categories
- [ ] Import categories from file
- [ ] Category model and table
- [ ] List categories endpoint
- [ ] Add category endpoint
- [ ] Track usage counts
- [ ] Frequent categories endpoint (top 15)

### Transaction CRUD
- [ ] List transactions for batch
- [ ] Update transaction (category, note)
- [ ] Bulk update transactions

### Categorization UI
- [ ] Transaction list table
- [ ] Sortable columns (date, amount, payee)
- [ ] Filter tabs (All/Uncategorized/Categorized)
- [ ] Row selection
- [ ] Category selector component:
  - [ ] Frequent categories buttons
  - [ ] Search input with filtering
  - [ ] Drill-down parent → child navigation
- [ ] Note input field
- [ ] Multi-select checkboxes
- [ ] Bulk categorize action

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
