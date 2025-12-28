#!/bin/bash
#
# Test CSV file upload directly
# Usage: ./test_upload_file.sh <path-to-csv-file>
#

if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-csv-file>"
    exit 1
fi

FILE_PATH="$1"

if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found: $FILE_PATH"
    exit 1
fi

echo "Testing CSV file: $FILE_PATH"
echo "========================================"

# Copy to container
echo "1. Copying file to container..."
docker cp "$FILE_PATH" categorizer:/tmp/test_upload.csv

# Test detection
echo -e "\n2. Testing format detection..."
docker exec categorizer python3 -c "
import sys; sys.path.insert(0, '/app')
from app.services.csv_parser import detect_csv_format

with open('/tmp/test_upload.csv', 'rb') as f:
    content = f.read()

print(f'File size: {len(content)} bytes')

try:
    fmt = detect_csv_format(content)
    print(f'✓ Detected format: {fmt}')
except ValueError as e:
    print(f'✗ Detection failed: {e}')
    print(f'First 100 bytes: {content[:100]}')
"

# Test parsing
echo -e "\n3. Testing CSV parsing..."
docker exec categorizer python3 -c "
import sys; sys.path.insert(0, '/app')
from app.services.csv_parser import get_parser

with open('/tmp/test_upload.csv', 'rb') as f:
    content = f.read()

try:
    parser = get_parser(content)
    transactions = parser.parse(content)
    print(f'✓ Successfully parsed {len(transactions)} transactions')

    if transactions:
        print(f'First transaction: {transactions[0].date} | {transactions[0].payee[:40]} | {transactions[0].amount}')
except Exception as e:
    print(f'✗ Parsing failed: {e}')
"

echo -e "\n========================================"
echo "Test complete!"
