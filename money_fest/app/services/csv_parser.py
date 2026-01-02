"""
CSV Parser for Money Fest - Supports multiple bank formats with auto-detection

Supported formats:
- AceMoney: latin-1 encoding, comma delimiter, withdrawal/deposit columns
- Danske Bank: UTF-8 encoding, semicolon delimiter, Danish decimal format
"""

import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ParsedTransaction:
    """Standardized transaction data from CSV parsing"""
    date: str          # YYYY-MM-DD (internal format)
    payee: str
    amount: float      # Negative for expenses, positive for income
    original_category: str = ""
    original_comment: str = ""


class CSVParser(ABC):
    """Abstract base class for CSV parsers"""

    @abstractmethod
    def parse(self, file_content: bytes) -> List[ParsedTransaction]:
        """Parse CSV file content and return list of transactions"""
        pass

    @abstractmethod
    def validate(self, file_content: bytes) -> List[str]:
        """
        Validate CSV file content
        Returns list of error messages (empty list if valid)
        """
        pass


class AceMoneyParser(CSVParser):
    """
    Parser for AceMoney CSV format

    Format:
    - Encoding: latin-1
    - Delimiter: comma
    - Headers: transaction,date,payee,category,status,withdrawal,deposit,total,comment
    - Date: DD.MM.YYYY or DD-MM-YYYY (both formats supported)
    - Amount: Separate withdrawal/deposit columns (only one populated)

    Note: Also accepts common variants like "Num" for "transaction" and "S" for "status"
    """

    EXPECTED_HEADERS = ['transaction', 'date', 'payee', 'category', 'status',
                       'withdrawal', 'deposit', 'total', 'comment']

    # Header aliases - maps variant names to canonical names
    HEADER_ALIASES = {
        'num': 'transaction',
        's': 'status'
    }

    @classmethod
    def normalize_header(cls, header: str) -> str:
        """Normalize header name, applying aliases if needed"""
        normalized = header.strip().lower()
        return cls.HEADER_ALIASES.get(normalized, normalized)

    def parse(self, file_content: bytes) -> List[ParsedTransaction]:
        """Parse AceMoney CSV file"""
        # Validate first
        errors = self.validate(file_content)
        if errors:
            raise ValueError(f"CSV validation failed: {'; '.join(errors)}")

        # Decode with latin-1
        try:
            text = file_content.decode('latin-1')
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode file with latin-1 encoding: {e}")

        # Parse CSV with normalized headers
        lines = text.split('\n')
        if not lines:
            raise ValueError("File is empty")

        # Get and normalize headers
        header_reader = csv.reader(io.StringIO(lines[0]))
        original_headers = next(header_reader)
        normalized_headers = [self.normalize_header(h) for h in original_headers]

        # Create DictReader with normalized headers
        # Re-read from start but use normalized fieldnames
        reader = csv.DictReader(io.StringIO(text), fieldnames=normalized_headers)
        next(reader)  # Skip the original header row
        transactions = []

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                # Parse date: Support multiple formats
                date_str = row['date'].strip()
                # Try multiple date formats (DD.MM.YYYY, DD-MM-YYYY, YYYY/MM/DD, YYYY-MM-DD)
                date_obj = None
                for fmt in ['%d.%m.%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue

                if not date_obj:
                    raise ValueError(f"Invalid date format '{date_str}' (expected DD.MM.YYYY, DD-MM-YYYY, YYYY/MM/DD, or YYYY-MM-DD)")

                date_internal = date_obj.strftime('%Y-%m-%d')

                # Get payee
                payee = row['payee'].strip()
                if not payee:
                    raise ValueError(f"Row {row_num}: Missing payee")

                # Calculate amount from withdrawal/deposit
                withdrawal = row['withdrawal'].strip()
                deposit = row['deposit'].strip()

                if withdrawal and deposit:
                    raise ValueError(f"Row {row_num}: Both withdrawal and deposit have values")
                elif withdrawal:
                    amount = -float(withdrawal)
                elif deposit:
                    amount = float(deposit)
                else:
                    # Skip rows with no amount (memo/note entries)
                    continue

                # Get original category and comment
                original_category = row.get('category', '').strip()
                original_comment = row.get('comment', '').strip()

                transactions.append(ParsedTransaction(
                    date=date_internal,
                    payee=payee,
                    amount=amount,
                    original_category=original_category,
                    original_comment=original_comment
                ))

            except ValueError as e:
                # Re-raise with row number if not already included
                if f"Row {row_num}" not in str(e):
                    raise ValueError(f"Row {row_num}: {e}")
                raise
            except KeyError as e:
                raise ValueError(f"Row {row_num}: Missing column {e}")

        if not transactions:
            raise ValueError("No transactions found in CSV file")

        return transactions

    def validate(self, file_content: bytes) -> List[str]:
        """Validate AceMoney CSV format"""
        errors = []

        # Check if file is empty
        if not file_content or len(file_content.strip()) == 0:
            errors.append("File is empty")
            return errors

        # Try to decode
        try:
            text = file_content.decode('latin-1')
        except UnicodeDecodeError as e:
            errors.append(f"Failed to decode file with latin-1 encoding: {e}")
            return errors

        # Parse CSV to check headers
        try:
            reader = csv.reader(io.StringIO(text))
            headers = next(reader)

            # Normalize headers (strip whitespace, lowercase, apply aliases)
            headers = [self.normalize_header(h) for h in headers]
            expected = [h.lower() for h in self.EXPECTED_HEADERS]

            if headers != expected:
                errors.append(
                    f"Invalid headers.\n"
                    f"Expected: {', '.join(self.EXPECTED_HEADERS)}\n"
                    f"Found: {', '.join(headers)}\n"
                    f"Note: Headers must match exactly (case-insensitive, 'Num' and 'S' are accepted as aliases)"
                )
        except StopIteration:
            errors.append("File contains no data (not even headers)")
        except Exception as e:
            errors.append(f"Failed to parse CSV: {e}")

        return errors


class DanskeBankParser(CSVParser):
    """
    Parser for Danske Bank CSV format

    Format:
    - Encoding: UTF-8 or ISO-8859-1 (both supported)
    - Delimiter: semicolon
    - Headers: "Dato";"Tekst";"Beløb";"Saldo";"Status";"Afstemt"
    - Date: DD.MM.YYYY
    - Amount: Single "Beløb" column with Danish decimal format (1.234,56)
    - Ignore: "Saldo" column (running balance)
    """

    EXPECTED_HEADERS = ['Dato', 'Tekst', 'Beløb', 'Saldo', 'Status', 'Afstemt']
    # Alternative headers for encoding-damaged files (ø might be corrupted)
    REQUIRED_HEADERS = ['Dato', 'Tekst', 'Saldo', 'Status']  # Must have these

    def parse(self, file_content: bytes) -> List[ParsedTransaction]:
        """Parse Danske Bank CSV file"""
        # Validate first
        errors = self.validate(file_content)
        if errors:
            raise ValueError(f"CSV validation failed: {'; '.join(errors)}")

        # Decode with UTF-8 or ISO-8859-1 (latin-1) as fallback
        text = None
        for encoding in ['utf-8', 'iso-8859-1']:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not text:
            raise ValueError("Failed to decode file with UTF-8 or ISO-8859-1 encoding")

        # Parse CSV with semicolon delimiter
        reader = csv.DictReader(io.StringIO(text), delimiter=';')
        transactions = []

        # Get the actual amount column name (might be "Beløb" or corrupted like "Bel�b")
        fieldnames = reader.fieldnames if reader.fieldnames else []
        amount_col = None
        for field in fieldnames:
            # Look for column that starts with "Bel" (handles encoding issues)
            if field.strip().strip('"').startswith('Bel'):
                amount_col = field
                break

        if not amount_col:
            raise ValueError("Could not find amount column (expected 'Beløb' or similar)")

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                # Parse date: DD.MM.YYYY → YYYY-MM-DD
                date_str = row['Dato'].strip().strip('"')
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                date_internal = date_obj.strftime('%Y-%m-%d')

                # Get payee (from "Tekst" column)
                payee = row['Tekst'].strip().strip('"')
                if not payee:
                    raise ValueError(f"Row {row_num}: Missing payee")

                # Parse amount from "Beløb" column with Danish decimal format
                # Format: "1.234,56" → 1234.56 or "-41,80" → -41.80
                amount_str = row[amount_col].strip().strip('"')
                if not amount_str:
                    # Skip rows with no amount (memo/note entries)
                    continue

                # Convert Danish decimal format to float
                # Remove thousand separators (periods) and replace decimal comma with period
                amount_str = amount_str.replace('.', '')  # Remove thousand separator
                amount_str = amount_str.replace(',', '.')  # Replace decimal comma with period
                amount = float(amount_str)

                # Get original category (Danske Bank doesn't have this, leave empty)
                original_category = ""
                original_comment = ""

                transactions.append(ParsedTransaction(
                    date=date_internal,
                    payee=payee,
                    amount=amount,
                    original_category=original_category,
                    original_comment=original_comment
                ))

            except ValueError as e:
                # Re-raise with row number if not already included
                if f"Row {row_num}" not in str(e):
                    raise ValueError(f"Row {row_num}: {e}")
                raise
            except KeyError as e:
                raise ValueError(f"Row {row_num}: Missing column {e}")

        if not transactions:
            raise ValueError("No transactions found in CSV file")

        return transactions

    def validate(self, file_content: bytes) -> List[str]:
        """Validate Danske Bank CSV format"""
        errors = []

        # Check if file is empty
        if not file_content or len(file_content.strip()) == 0:
            errors.append("File is empty")
            return errors

        # Try to decode with UTF-8 or ISO-8859-1
        text = None
        for encoding in ['utf-8', 'iso-8859-1']:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not text:
            errors.append("Failed to decode file with UTF-8 or ISO-8859-1 encoding")
            return errors

        # Parse CSV to check headers (semicolon delimiter)
        try:
            reader = csv.reader(io.StringIO(text), delimiter=';')
            headers = next(reader)

            # Normalize headers (strip whitespace and quotes)
            headers = [h.strip().strip('"') for h in headers]

            # Check if it matches expected headers exactly
            if headers == self.EXPECTED_HEADERS:
                return errors  # Perfect match

            # Check if required headers are present (allows encoding issues with ø/å)
            if all(req in headers for req in self.REQUIRED_HEADERS):
                # Has required headers, acceptable
                return errors

            errors.append(f"Invalid headers. Expected: {'; '.join(self.EXPECTED_HEADERS)}")
        except StopIteration:
            errors.append("File contains no data (not even headers)")
        except Exception as e:
            errors.append(f"Failed to parse CSV: {e}")

        return errors


def detect_csv_format(file_content: bytes) -> str:
    """
    Auto-detect CSV format from file content

    Returns:
        "danske_bank" or "acemoney"

    Raises:
        ValueError if format cannot be detected
    """
    if not file_content or len(file_content.strip()) == 0:
        raise ValueError("File is empty")

    # Try Danske Bank first (UTF-8 or ISO-8859-1 + semicolon)
    for encoding in ['utf-8', 'iso-8859-1']:
        try:
            text = file_content.decode(encoding)
            # Check if it uses semicolon delimiter
            if ';' in text.split('\n')[0]:
                # Check if headers match Danske Bank format
                reader = csv.reader(io.StringIO(text), delimiter=';')
                headers = next(reader)
                headers = [h.strip().strip('"') for h in headers]
                # Check exact match or required headers (allows for encoding issues)
                if (headers == DanskeBankParser.EXPECTED_HEADERS or
                    all(req in headers for req in DanskeBankParser.REQUIRED_HEADERS)):
                    return "danske_bank"
        except (UnicodeDecodeError, StopIteration):
            continue

    # Try AceMoney (latin-1 + comma)
    try:
        text = file_content.decode('latin-1')
        # Check if it uses comma delimiter
        if ',' in text.split('\n')[0]:
            # Check if headers match AceMoney format (with aliases)
            reader = csv.reader(io.StringIO(text))
            headers = next(reader)
            headers = [AceMoneyParser.normalize_header(h) for h in headers]
            expected = [h.lower() for h in AceMoneyParser.EXPECTED_HEADERS]
            if headers == expected:
                return "acemoney"
    except (UnicodeDecodeError, StopIteration):
        pass

    # Could not detect format
    raise ValueError(
        "Could not detect CSV format. File must be either AceMoney "
        "(latin-1, comma-delimited) or Danske Bank (UTF-8, semicolon-delimited) format"
    )


def get_parser(file_content: bytes) -> CSVParser:
    """
    Factory function to get the appropriate parser for a CSV file

    Args:
        file_content: Raw bytes of CSV file

    Returns:
        Appropriate CSVParser instance

    Raises:
        ValueError if format cannot be detected
    """
    format_type = detect_csv_format(file_content)

    if format_type == "acemoney":
        return AceMoneyParser()
    elif format_type == "danske_bank":
        return DanskeBankParser()
    else:
        raise ValueError(f"Unknown format type: {format_type}")


class CSVGenerator:
    """
    Generate CSV files in AceMoney format for export

    Always exports in AceMoney format regardless of original source format
    """

    def generate(self, transactions: List[dict]) -> bytes:
        """
        Generate AceMoney CSV from transactions

        Args:
            transactions: List of transaction dicts with keys:
                - date (str): YYYY-MM-DD format
                - payee (str)
                - amount (float): Negative for expenses, positive for income
                - category (str, optional)
                - note (str, optional)

        Returns:
            CSV file content as bytes (latin-1 encoded)
        """
        output = io.StringIO()

        # Write headers
        headers = ['transaction', 'date', 'payee', 'category', 'status',
                  'withdrawal', 'deposit', 'total', 'comment']
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        # Write transactions
        for txn in transactions:
            # Convert date: YYYY-MM-DD → DD.MM.YYYY
            date_obj = datetime.strptime(txn['date'], '%Y-%m-%d')
            date_display = date_obj.strftime('%d.%m.%Y')

            # Split amount into withdrawal/deposit
            amount = txn['amount']
            withdrawal = f"{abs(amount):.2f}" if amount < 0 else ""
            deposit = f"{amount:.2f}" if amount >= 0 else ""

            # Get category and note
            category = txn.get('category', '')
            note = txn.get('note', '')

            writer.writerow({
                'transaction': '',
                'date': date_display,
                'payee': txn['payee'],
                'category': category,
                'status': '',
                'withdrawal': withdrawal,
                'deposit': deposit,
                'total': '',
                'comment': note
            })

        # Encode as latin-1 and return bytes
        csv_text = output.getvalue()
        return csv_text.encode('latin-1')
