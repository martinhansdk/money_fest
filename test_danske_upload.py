"""
Quick test script to verify Danske Bank CSV parsing works
"""

# Read the Danske Bank example file
with open('/mnt/hgfs/exports/example_from_bank.csv', 'rb') as f:
    content = f.read()

print("File content (first 500 bytes):")
print(content[:500])
print("\n")

# Test auto-detection
from app.services.csv_parser import detect_csv_format, get_parser

try:
    format_type = detect_csv_format(content)
    print(f"Detected format: {format_type}")

    parser = get_parser(content)
    print(f"Parser type: {type(parser).__name__}")

    transactions = parser.parse(content)
    print(f"\nSuccessfully parsed {len(transactions)} transactions")

    print("\nFirst transaction:")
    t = transactions[0]
    print(f"  Date: {t.date}")
    print(f"  Payee: {t.payee}")
    print(f"  Amount: {t.amount}")

    print("\nAll transactions:")
    for i, t in enumerate(transactions):
        print(f"  {i+1}. {t.date} | {t.payee:30s} | {t.amount:10.2f}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
