# AGENTS.md - Transaction Categorizer

## Project Overview

A self-hosted web application for categorizing bank transactions on mobile devices. Designed for a couple to collaboratively categorize transactions in small batches, with real-time synchronization.

## Problem Being Solved

The user currently:
1. Downloads bank transactions as CSV monthly
2. Runs a Python script to transform the CSV
3. Imports into AceMoney (Windows software)
4. Manually categorizes transactions in AceMoney

The friction of needing to be at a PC creates backlogs of months of uncategorized transactions. This app moves the categorization step to mobile, enabling quick categorization during idle moments.

## Core User Flow

```
Bank CSV (latin-1) → Upload to app with custom name → Categorize on phone → Download CSV with categories → Import to AceMoney
```

## Key Requirements

### Must Have
- Mobile-friendly web UI (responsive, works on Android Chrome)
- Two user accounts with passwords
- Real-time sync via WebSocket (both users see updates instantly)
- Batch management (upload, list, download, delete, archive)
- Category selection: frequent buttons, search, drill-down
- Rules engine for payee-based suggestions
- Similar transaction lookup (by payee, by amount)
- Self-hosted in Docker container

### Technical Constraints
- CSV encoding: latin-1
- CSV format: `transaction,date,payee,category,status,withdrawal,deposit,total,comment`
- Date format in CSV: DD.MM.YYYY
- Category format: `Parent` or `Parent:Subcategory`
- 175 categories total (33 top-level, 142 subcategories)
- ~100 transactions per month

## Architecture Decision: Keep It Simple

This is a personal tool for two users with ~100 transactions/month. Avoid over-engineering:
- SQLite, not PostgreSQL
- Single container, not microservices
- Server-rendered HTML with minimal JS, not a SPA framework
- WebSocket for live updates only, not full state management

## Files to Reference

- `ARCHITECTURE.md` - System design and data model
- `REQUIREMENTS.md` - Detailed feature specifications
- `TODO.md` - Implementation checklist
- `TESTING.md` - Testing strategy
- `categories.txt` - Full category list
- `sample.csv` - Example CSV format

## Development Notes

### Priority Order
1. Core batch upload/download flow
2. Basic categorization UI
3. WebSocket sync
4. Rules engine
5. Similar transactions
6. Polish (celebrations, UX improvements)

### Known Challenges
- Payee field is messy (contains transaction IDs, terminal numbers)
- Same subcategory name can exist under multiple parents (e.g., Automobile:Maintenance, Household:Maintenance)
- Multiple rules may match same transaction - show all suggestions

### User Preferences
- List view for transactions (not card/one-at-a-time)
- Suggestions from rules should require confirmation (not auto-apply)
- Editable payee pattern when creating rules
- Archive automatically on download
- Small celebration animation when batch reaches 100%
