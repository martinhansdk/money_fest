# Money Fest Add-on Documentation

## Configuration Options

### port
**Type:** Port number
**Default:** 1111
**Description:** The network port where Money Fest will be accessible.

Access the application at `http://homeassistant.local:<port>` or `http://<your-ha-ip>:<port>`

### secret_key
**Type:** Password (required)
**Description:** Secret key for session signing and security.

**Important:** This must be set before starting the add-on.

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### session_max_age
**Type:** Integer (seconds)
**Default:** 2592000 (30 days)
**Range:** 86400 - 7776000 (1 day - 90 days)
**Description:** How long user sessions remain valid without activity.

### log_level
**Type:** List (debug|info|warning|error)
**Default:** info
**Description:** Logging verbosity level.

- **debug**: Detailed debugging information
- **info**: General informational messages
- **warning**: Warning messages only
- **error**: Error messages only

### auto_import_categories
**Type:** Boolean
**Default:** true
**Description:** Automatically import the default 175 categories on first run.

Set to false if you want to manually import or use custom categories.

### ssl_enabled
**Type:** Boolean
**Default:** false
**Description:** Enable HTTPS with automatic self-signed certificate generation.

When enabled, Money Fest will:
- Automatically generate a self-signed SSL certificate on first run
- Save it to `/data/certs/` (persistent storage)
- Reuse the same certificate on subsequent starts
- Start the web server with HTTPS instead of HTTP

**Usage:**
1. Enable this option in add-on configuration
2. Restart the add-on
3. Access via `https://[YOUR-HA-IP]:[PORT]`

**Note:** Your browser will show a security warning for self-signed certificates. This is normal for home use. You can install the certificate on your devices to remove the warning (see Security section below).

## First-Time Setup

### Step 1: Configure the Add-on

1. Open the Money Fest add-on configuration
2. Set a strong **secret_key** (required!)
3. Optionally adjust other settings (port, session age, etc.)
4. Save the configuration

### Step 2: Start the Add-on

Click "Start" to launch the Money Fest add-on.

### Step 3: Create Your First User

After the add-on starts, check the logs for the setup URL, then:

1. Find your Home Assistant IP address:
   - Settings → System → Network

2. Open your browser and navigate to:
   - `http://[YOUR-HA-IP]:[PORT]/setup` (or `https://` if SSL is enabled)
   - Example: `http://192.168.1.100:1111/setup`
   - Or: `http://homeassistant.local:1111/setup`

3. Fill out the setup form:
   - **Username**: 3-50 characters
   - **Password**: 8+ characters
   - **Confirm Password**: Must match

4. Click "Create User"

5. You'll be redirected to the login page

6. Log in with your new credentials!

**Security Note**: The `/setup` page becomes inaccessible after the first user is created.

### Step 4: Create Additional Users (Optional)

For collaborative use with a partner, you have two options:

**Option 1: Web Interface (Easiest)**

1. Log in to Money Fest
2. Click the "Users" button in the header
3. Fill out the create user form
4. Click "Create User"

**Option 2: CLI**

```bash
ha addons exec money_fest python -m app.cli create-user julia --password herpassword456
```

Or use interactive mode (if you have SSH add-on):
```bash
ha addons exec money_fest python -m app.cli create-user julia
# You'll be prompted to enter password securely
```

## CLI Commands

All CLI commands are run using `ha addons exec money_fest`:

### create-user
Create a new user account.

**Syntax:**
```bash
ha addons exec money_fest python -m app.cli create-user <username> --password <password>
```

**Example:**
```bash
ha addons exec money_fest python -m app.cli create-user martin --password mypassword123
```

**Interactive mode** (requires SSH add-on):
```bash
ha addons exec money_fest python -m app.cli create-user martin
```

### reset-password
Reset a user's password.

**Syntax:**
```bash
ha addons exec money_fest python -m app.cli reset-password <username> --password <newpassword>
```

**Example:**
```bash
ha addons exec money_fest python -m app.cli reset-password martin --password newpassword456
```

### import-categories
Manually import categories from a file.

**Syntax:**
```bash
ha addons exec money_fest python -m app.cli import-categories /app/categories.txt
```

**Note**: Categories are auto-imported on first run if `auto_import_categories` is enabled.

### backup
Create a database backup.

**Syntax:**
```bash
ha addons exec money_fest python -m app.cli backup /share/
```

**Example:**
```bash
ha addons exec money_fest python -m app.cli backup /share/
# Creates: /share/categorizer_backup_YYYYMMDD_HHMMSS.db
```

Backup will be saved to your Home Assistant share folder, accessible via:
- File Editor add-on
- Samba/SMB share
- SSH add-on

## Data Persistence

Your database is stored at `/data/categorizer.db` inside the add-on container. This is automatically persisted by Home Assistant across add-on updates and restarts.

### Backups

**Automatic:** Your data is included in Home Assistant's automatic backup system.

**Manual CLI Backup:**
```bash
# Backup to share folder (accessible from file editor or samba)
ha addons exec money_fest python -m app.cli backup /share/

# Backup filename format: categorizer_backup_YYYYMMDD_HHMMSS.db
```

**Restoring from Backup:**
1. Stop the Money Fest add-on
2. Copy your backup file to the add-on's data directory (advanced, requires SSH)
3. Start the add-on

## CSV File Formats

Money Fest automatically detects and supports two CSV formats:

### AceMoney Format
```csv
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,Grocery Store,,,100.50,,,
,25.07.2023,Restaurant,,,45.00,,,
```

**Characteristics:**
- Date format: DD.MM.YYYY or DD-MM-YYYY
- Amount in `withdrawal` or `deposit` columns
- Latin-1 or UTF-8 encoding

### Danske Bank Format
```csv
"Dato";"Tekst";"Beløb";"Saldo";"Status";"Afstemt"
"25.11.2024";"Grocery Store";"-41,80";"98.302,29";"Udført";"Nej"
"26.11.2024";"Salary";"5.000,00";"103.302,29";"Udført";"Nej"
```

**Characteristics:**
- Date format: DD.MM.YYYY or DD-MM-YYYY
- Amount in `Beløb` column with comma decimals (e.g., "-41,80")
- Semicolon delimited
- UTF-8 or ISO-8859-1 encoding

Both formats are automatically detected. Simply upload and Money Fest will handle it!

## Using Money Fest

### Upload a Batch

1. Log in to Money Fest
2. Click "Upload CSV" button
3. Select your bank's CSV export file
4. The batch will be created with transaction details
5. Start categorizing!

### Categorize Transactions

1. Select one or more transactions using checkboxes
2. Choose a category from:
   - **Frequent categories** (top 15 most-used)
   - **Search** for categories by name
   - **Browse** hierarchical categories
3. Optionally add a note
4. Click "Categorize Selected"

### Real-Time Collaboration

If two users are logged in simultaneously:
- Changes made by one user appear instantly for the other
- Toast notifications show when your partner categorizes transactions
- Confetti celebration when batch is complete!

### Create Rules

After categorizing transactions, create rules to auto-suggest categories:

1. Go to Rules page
2. Click "Create Rule"
3. Set pattern (e.g., "GROCERY STORE")
4. Choose match type:
   - **Contains**: Matches if payee contains the pattern
   - **Exact**: Matches only exact payee names
5. Select category
6. Preview shows matching transactions
7. Save rule

Rules will show as gold-colored suggestions when categorizing future transactions.

### Find Similar Transactions

Click "Show similar" on any transaction to find:
- **Similar by payee**: Fuzzy name matching
- **Similar by amount**: Within configurable tolerance
- **Context**: Surrounding transactions by date

Bulk categorize similar transactions together!

### Download Categorized CSV

1. When batch is complete (100% categorized)
2. Click "Download CSV"
3. File downloads in AceMoney format
4. Batch is automatically archived

Archived batches can be viewed by toggling "Include archived" on the batches page.

## Accessing from Mobile Devices

1. Ensure your mobile device is on the same network as Home Assistant
2. Find your Home Assistant IP address (Settings → System → Network)
3. Access: `http://<ha-ip>:<port>` (e.g., `http://192.168.1.100:1111`)

**Tip:** Add the page to your mobile home screen for app-like experience.

**On iOS:**
1. Open Safari
2. Tap the Share button
3. Select "Add to Home Screen"

**On Android:**
1. Open Chrome
2. Tap the menu (three dots)
3. Select "Add to Home screen"

## Troubleshooting

### Can't access the web interface

1. Check the add-on is running (green "Running" status)
2. Check logs for errors: Add-on → Logs tab
3. Verify port is not used by another service
4. Try accessing via IP address instead of .local name
5. Check firewall settings if accessing from external network

### Setup page (/setup) redirects to login

This is normal after the first user is created. The setup page is only accessible when no users exist (for security).

To create additional users, use the CLI:
```bash
ha addons exec money_fest python -m app.cli create-user <username> --password <password>
```

### No categories available

If categories weren't imported automatically:

```bash
ha addons exec money_fest python -m app.cli import-categories /app/categories.txt
```

### Forgot password

Reset using CLI:

```bash
ha addons exec money_fest python -m app.cli reset-password <username> --password <newpassword>
```

### Database corruption

If the database becomes corrupted:

1. **First, backup your data** if possible:
   ```bash
   ha addons exec money_fest python -m app.cli backup /share/
   ```

2. Stop the add-on

3. Contact support or restore from Home Assistant backup

**Note:** Always keep regular backups!

### Upload CSV fails

1. Check the CSV format is supported (AceMoney or Danske Bank)
2. Verify the file encoding (UTF-8, Latin-1, or ISO-8859-1)
3. Check logs for detailed error messages
4. Ensure the CSV has the required columns

### WebSocket connection issues

If real-time sync isn't working:
1. Check browser console for errors (F12)
2. Verify both users are on the same batch
3. Check add-on logs for WebSocket errors
4. Try refreshing the page

## Security Notes

- Money Fest uses its own authentication (not Home Assistant auth)
- Passwords are hashed with bcrypt before storage
- Sessions use secure random tokens signed with your secret key
- Default setup uses HTTP (not HTTPS)
  - For HTTPS, use a reverse proxy like nginx-proxy-manager
  - Or access through Home Assistant's proxy if available
- The `/setup` endpoint is automatically disabled after first user creation

## Advanced Configuration

### Custom Port

Change the `port` option in add-on configuration. Useful if port 1111 conflicts with another service.

### Shorter Session Time

For security-conscious users, reduce `session_max_age` to force more frequent logins.

### Debugging

Set `log_level` to `debug` to see detailed information about:
- HTTP requests and responses
- Database operations
- WebSocket connections
- CSV parsing details

## Integration with Home Assistant

Money Fest runs as a standalone web application and does not create Home Assistant entities or services. It's a self-contained financial tool accessible via its own web interface.

If you want to access Money Fest from Home Assistant's sidebar, you can add it manually:
1. Settings → Dashboards
2. Add a "Webpage" card with the Money Fest URL

## Performance

Money Fest is designed for personal/couple use:
- Handles thousands of transactions efficiently
- SQLite database with optimized indexes
- WebSocket connections are lightweight
- Minimal memory footprint (~50-100MB)

For very large batches (>1000 transactions), categorization may take longer but will remain responsive.

## Data Privacy

All data stays local:
- Database stored in your Home Assistant add-on data directory
- No external services or cloud connections
- No analytics or tracking
- CSV files processed locally

## Security

### HTTPS/SSL Certificates

When `ssl_enabled` is true, Money Fest automatically generates and uses self-signed SSL certificates:

**Certificate Storage:**
- Location: `/data/certs/cert.pem` and `/data/certs/key.pem`
- Persistence: Certificates persist across add-on restarts and updates
- Validity: 3650 days (10 years)

**Browser Warnings:**
Self-signed certificates will trigger browser security warnings. This is expected and normal for home use. You have two options:

1. **Accept the warning** each time (safest for home use)
2. **Install the certificate** on your devices to remove warnings

**Installing the Certificate:**

To copy the certificate from the add-on:
```bash
# View certificate path in add-on data
ha addons info money_fest
```

The certificate is in `/data/certs/cert.pem` within the add-on's data directory.

**When to Use HTTPS:**
- Accessing Money Fest over your local network (recommended)
- Accessing from mobile devices
- Extra peace of mind for password transmission

**When HTTP is OK:**
- Accessing only from localhost
- Isolated home network with no guests
- Using a reverse proxy that handles SSL

### Password Security

- Passwords are hashed with bcrypt (industry standard)
- Session tokens are cryptographically signed with your secret key
- Session cookies are secure and HTTP-only
- Passwords never appear in logs

**Best Practices:**
- Use a strong, unique password for each user
- Keep your `secret_key` secure and never share it
- Use different passwords than your Home Assistant login
- Consider using HTTPS if accessing over WiFi

### Network Security

Money Fest uses **separate port access** (not Ingress), which means:
- Accessible directly via IP:PORT
- Not protected by Home Assistant authentication
- Can be firewalled separately if needed
- Consider restricting access to local network only

## Support & Development

- **GitHub:** [martinhansdk/money_fest](https://github.com/martinhansdk/money_fest)
- **Issues:** Report bugs and request features on GitHub
- **Documentation:** Full docs available in repository

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
