# Requirements Specification

## 1. Authentication

### 1.1 User Accounts
- Two user accounts with username and password
- Accounts created via CLI command or first-run setup
- No registration flow (private system)

### 1.2 Login
- Simple login form: username, password
- Session-based authentication (cookie)
- "Remember me" option (longer session duration)
- Redirect to batch list on success

### 1.3 Session Management
- Sessions expire after 30 days of inactivity
- Logout clears session
- All API endpoints require authentication except login

---

## 2. Batch Management

### 2.1 Batch List View
- Shows all non-archived batches by default
- Toggle to include archived batches
- For each batch, display:
  - Name (user-provided on upload)
  - Date range (earliest to latest transaction date)
  - Progress: "47/103" and percentage bar
  - Status indicator (in progress / complete)
  - Uploaded by and upload date

### 2.2 Batch Upload
- File picker for CSV file
- Text input for batch name
- Upload button
- CSV parsing:
  - Encoding: latin-1
  - Columns: transaction, date, payee, category, status, withdrawal, deposit, total, comment
  - Date parsing: DD.MM.YYYY format
  - Amount: withdrawal column (expense) or deposit column (income)
  - Skip header row
- On success: redirect to categorize view
- On error: show parsing errors, don't create batch

### 2.3 Batch Download
- Downloads CSV with same format as input
- Category column filled in for categorized transactions
- Comment column contains note if set
- Triggers auto-archive of the batch
- Filename: original name + "_categorized.csv"

### 2.4 Batch Delete
- Confirmation dialog: "Delete batch 'November 2024' and all 103 transactions?"
- Hard delete (no soft delete)
- Available for any non-archived batch

### 2.5 Batch Archive/Unarchive
- Archived batches hidden from default list view
- Toggle filter to show archived
- Unarchive action available on archived batches
- Archive happens automatically on download

### 2.6 Batch Completion Celebration
- When a batch reaches 100% categorized:
  - Brief animation (confetti, checkmark, or similar)
  - Toast message: "🎉 Batch complete!"
  - Batch card updates to show "Complete" status
- Celebration triggers for whoever categorizes the last transaction
- Also broadcast to other connected user via WebSocket

---

## 3. Transaction Categorization

### 3.1 Transaction List View
- Shows all transactions in selected batch
- Table columns:
  - Date
  - Payee
  - Amount (color-coded: red for expense, green for income)
  - Category (empty, suggested, or assigned)
  - Status indicator (uncategorized / suggested / categorized)
- Sortable by date (default), amount, payee
- Filterable: All / Uncategorized / Categorized
- Uncategorized count displayed prominently

### 3.2 Category Assignment
- Click/tap a transaction row to select it
- Category selector appears (see 3.4)
- Select category → transaction updated
- Move to next uncategorized transaction automatically (optional setting)
- Visual feedback: row updates immediately

### 3.3 Rule-Based Suggestions
- On load, match all transactions against rules
- Transactions with matches show:
  - Suggested category(ies) as clickable chips
  - "Suggested" status indicator
- If multiple rules match, show all suggestions
- Tap suggestion to accept (one tap categorization)
- Tap elsewhere to open full category selector

### 3.4 Category Selector
Three-tier selection UI:

**Tier 1: Frequent Categories (Quick Access)**
- Top 10-15 most used categories as buttons
- Based on usage_count from database
- Single tap to select

**Tier 2: Search**
- Text input with instant filter
- Searches full path: "main" matches "Automobile:Maintenance"
- Shows matching categories as list
- Tap to select

**Tier 3: Drill-down**
- List of 33 parent categories
- Tap parent to see its subcategories
- Tap subcategory to select
- Back button to return to parent list

### 3.5 Notes
- Optional note field for each transaction
- Editable when transaction is selected
- Saved alongside category
- Maps to "comment" field in CSV export

### 3.6 Multi-Select Categorization
- Checkbox on each transaction row
- "Select all visible" option
- With selection active:
  - Category selector applies to all selected
  - "Clear selection" button
- Use case: categorize 5 similar grocery store transactions at once

---

## 4. Similar Transactions

### 4.1 Similar by Payee
- Button/link on transaction: "Show similar"
- Panel shows transactions with similar payee text:
  - Fuzzy match (contains, case-insensitive)
  - From all batches (including archived)
- Display: date, payee, amount, category (if assigned), batch name
- Selectable for batch categorization

### 4.2 Similar by Amount
- Option in similar panel: "By amount"
- Shows transactions within ±10% of amount
- Same display format as payee matches

### 4.3 Surrounding Transactions
- Button: "Show context"
- Shows 5 transactions before and after (by date) from same batch
- Helps remember: "what else did I buy that day?"
- Display inline or as expandable section

---

## 5. Rules Engine

### 5.1 Rule Structure
- Pattern: text to match in payee field
- Match type: "contains" (default) or "exact"
- Category: the category to suggest
- Created by: which user created it

### 5.2 Rule Creation
- From transaction: "Create rule" button
- Modal/form:
  - Pattern field, pre-filled with transaction's payee
  - Editable - user cleans up: "IKEA ))) 72547" → "IKEA"
  - Match type dropdown: contains / exact
  - Category pre-filled from transaction's assigned category
- Save creates rule, applies to future matches

### 5.3 Rule Management
- Rules list view (separate page/modal)
- Shows: pattern, match type, category, created by
- Delete button for each rule
- No edit (delete and recreate)

### 5.4 Rule Matching
- Case-insensitive
- "Contains" checks if pattern appears anywhere in payee
- "Exact" checks full payee equals pattern
- Multiple rules can match same transaction
- All matches shown as suggestions

---

## 6. Categories

### 6.1 Category Structure
- Two levels max: Parent or Parent:Subcategory
- 175 total categories provided (see categories.txt)
- Stored with full_path for unique identification

### 6.2 Category Display
- Always show full path in lists: "Clothing:Shoes"
- In frequent buttons, can abbreviate if parent is clear

### 6.3 Add New Category
- Accessible from category selector: "+ Add category"
- Form: Parent dropdown + Subcategory name (optional)
- Or: full path text input
- Validates uniqueness
- Immediately available for selection

### 6.4 Usage Tracking
- Increment usage_count when category is assigned
- Decrement when changed away (optional, simpler to not bother)
- Used for sorting frequent categories

---

## 7. Real-Time Sync

### 7.1 WebSocket Connection
- Established on page load
- Reconnects automatically on disconnect
- Subscribes to currently viewed batch

### 7.2 Events Broadcast
- Transaction categorized: other user sees update instantly
- Batch progress changes: progress bar updates
- Batch complete: both users see celebration
- New batch uploaded: appears in batch list

### 7.3 Conflict Handling
- Last write wins (simple)
- If both users categorize same transaction simultaneously:
  - Both see final state
  - No error, just latest value
- Acceptable given trust between users

---

## 8. CSV Format

### 8.1 Input Format
```
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,DSB NETBUTIK       09589,,,160.0,,,
,21.07.2023,ALDI Øst 090       00395,,,146.45,,,
,27.07.2023,Lønoverførsel,,,,28511.61,,
```

- Encoding: latin-1
- First column (transaction) always empty
- Date: DD.MM.YYYY
- Payee: may contain special characters, numbers
- Category: empty on import, filled on export
- Withdrawal: expense amount (positive number)
- Deposit: income amount (positive number)
- Comment: maps to note field

### 8.2 Output Format
- Same structure as input
- Category column populated
- Comment column contains note if set
- Preserve original encoding (latin-1)

---

## 9. Mobile UX

### 9.1 Responsive Design
- Works on phones (360px+), tablets, desktop
- Touch-friendly tap targets (44px minimum)
- No hover-dependent interactions

### 9.2 Performance
- Fast initial load (<2s on 3G)
- Instant feedback on interactions
- Optimistic UI updates

### 9.3 Offline
- Not required (home network assumed)
- Graceful handling of connection loss
- Reconnect and sync on restore

---

## 10. Initial Setup

### 10.1 First Run
- Detect empty database
- Prompt to create two user accounts
- Import categories from bundled list

### 10.2 CLI Commands
```bash
# Create user
docker exec categorizer python -m app.cli create-user <username>

# Import categories
docker exec categorizer python -m app.cli import-categories /path/to/categories.txt

# Export database backup
docker exec categorizer python -m app.cli backup /path/to/backup.db
```
