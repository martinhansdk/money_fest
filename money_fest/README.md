# Money Fest - Collaborative Transaction Categorizer

A self-hosted web application for collaborative bank transaction categorization on mobile devices.
Built for couples to jointly categorize their bank transactions in small batches using smartphones,
with real-time synchronization.

## About

Money Fest allows two users to:
- Upload bank transaction CSV files (AceMoney & Danske Bank formats)
- Categorize transactions into 175+ predefined categories
- Collaborate in real-time with WebSocket synchronization
- Create smart categorization rules
- Find similar transactions for batch categorization
- Export categorized data back to CSV

Perfect for couples managing shared finances!

## Features

- **Multi-format CSV Support**: Auto-detects AceMoney and Danske Bank formats
- **Real-time Collaboration**: WebSocket-based sync between devices
- **Smart Categorization**: Rule-based suggestions and similar transaction matching
- **Mobile-Optimized UI**: Works great on smartphones
- **Secure Authentication**: Session-based auth with bcrypt password hashing
- **Batch Management**: Organize transactions in batches with progress tracking

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Money Fest" add-on
3. Configure your secret key (required)
4. Start the add-on
5. Visit the web setup page to create your first user

## Configuration

See the "Documentation" tab for detailed configuration options.

**Important**: You must set a strong secret key before first use.

Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## First-Time Setup

After starting the add-on for the first time:

1. Check the add-on logs for the setup URL
2. Visit `http://[YOUR-HA-IP]:[PORT]/setup` in your browser
3. Create your first user (username and password)
4. You'll be redirected to the login page
5. Log in and start categorizing!

**Create additional users** later using the CLI:
```bash
ha addons exec money_fest python -m app.cli create-user <username> --password <password>
```

Example:
```bash
ha addons exec money_fest python -m app.cli create-user julia --password herpassword456
```

## Quick Start

1. **Configure**: Set a strong secret key in the add-on configuration
2. **Start**: Start the add-on
3. **Setup**: Visit `/setup` to create your first user
4. **Login**: Log in with your credentials
5. **Upload**: Upload a CSV file from your bank
6. **Categorize**: Start categorizing transactions!

## Access

The web interface will be available at:
- `http://homeassistant.local:[PORT]` (if using .local addresses)
- `http://[YOUR-HA-IP]:[PORT]` (replace with your Home Assistant IP)

Default port is 1111 (configurable in add-on options).

## Support

For issues and questions, visit: [GitHub Issues](https://github.com/martinhansdk/money_fest/issues)

## Documentation

Full documentation is available in the "Documentation" tab of this add-on.
