# CSV Format Troubleshooting Guide

## AceMoney CSV Format Requirements

The CSV parser expects **exact headers** in this order:

```
transaction,date,payee,category,status,withdrawal,deposit,total,comment
```

### Common Issues

1. **Wrong encoding**: File must be **latin-1** (ISO-8859-1) encoded
2. **Wrong delimiter**: Must use **commas** (`,`) not semicolons
3. **Missing headers**: All 9 columns must be present
4. **Wrong header names**: Headers must match exactly (case-insensitive but names must match)
5. **Wrong order**: Headers must be in the exact order shown above

### Example of Valid AceMoney CSV

```csv
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,25-11-2024,Netto ScanNGo,,,41.8,,,
,25-11-2024,Grocery Store,,,609.01,,,
,26-11-2024,Restaurant,,,240.0,,,
```

### How to Check Your File

Run these commands to diagnose the issue:

```bash
# Check encoding
file your_file.csv

# View first line (headers)
head -1 your_file.csv

# Check delimiter (should show commas)
head -1 your_file.csv | od -c
```

### If You Get Format Errors

The error message now shows:
- **Expected headers**: What the parser needs
- **Found headers**: What your file actually has
- **Comparison**: So you can see the difference

### Converting from Other Formats

If your file is in a different format:

1. **Danske Bank format** is auto-detected (semicolon delimiter, UTF-8)
2. **Other formats** need to be converted to AceMoney format first

### Quick Fix Options

1. **Excel/LibreOffice**:
   - Open the CSV
   - Add/rename headers to match required format
   - Save As > CSV (Comma delimited)
   - Choose "Western European (ISO-8859-1)" encoding

2. **Command line** (Linux/Mac):
   ```bash
   # Convert UTF-8 to latin-1
   iconv -f UTF-8 -t ISO-8859-1 input.csv > output.csv
   ```

### Supported Date Formats

- `DD.MM.YYYY` (e.g., 25.11.2024)
- `DD-MM-YYYY` (e.g., 25-11-2024)

### Amount Columns

- **withdrawal**: Negative amounts (expenses) - put value without minus sign
- **deposit**: Positive amounts (income) - put value
- Only one should have a value per row
- Use decimal point (`.`) not comma

### Example Conversion

**Wrong (UTF-8, semicolon):**
```csv
Date;Merchant;Amount
2024-11-25;Store;-42.50
```

**Correct (latin-1, comma):**
```csv
transaction,date,payee,category,status,withdrawal,deposit,total,comment
,25-11-2024,Store,,,42.50,,,
```
