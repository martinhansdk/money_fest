"""
Tests for CSV parser service - supports AceMoney and Danske Bank formats
"""

import pytest
from app.services.csv_parser import (
    ParsedTransaction,
    AceMoneyParser,
    DanskeBankParser,
    CSVGenerator,
    detect_csv_format,
    get_parser
)


# Sample AceMoney CSV content (latin-1 encoded)
ACEMONEY_SAMPLE = b"""transaction,date,payee,category,status,withdrawal,deposit,total,comment
,21.07.2023,DSB NETBUTIK,,,160.0,,,
,27.07.2023,L\xf8noverf\xf8rsel,,,,28511.61,,Monthly salary
,15.08.2023,Netto,,,45.50,,,,
"""

# Sample Danske Bank CSV content (UTF-8 encoded)
DANSKE_BANK_SAMPLE = b""""Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"
"25.11.2024";"Netto ScanNGo";"-41,80";"98.302,29";"Udf\xc3\xb8rt";"Nej"
"25.11.2024";"433 Netto Hedehuse";"-609,01";"97.693,28";"Udf\xc3\xb8rt";"Nej"
"26.11.2024";"L\xc3\xb8n";"28.500,00";"126.193,28";"Udf\xc3\xb8rt";"Nej"
"""


class TestAceMoneyParser:
    """Tests for AceMoney CSV parser"""

    def test_parse_valid(self):
        """Test parsing a valid AceMoney CSV"""
        parser = AceMoneyParser()
        transactions = parser.parse(ACEMONEY_SAMPLE)

        assert len(transactions) == 3

        # Check first transaction (withdrawal)
        assert transactions[0].date == "2023-07-21"
        assert transactions[0].payee == "DSB NETBUTIK"
        assert transactions[0].amount == -160.0
        assert transactions[0].original_category == ""
        assert transactions[0].original_comment == ""

        # Check second transaction (deposit with category and comment)
        assert transactions[1].date == "2023-07-27"
        assert transactions[1].payee == "Lønoverførsel"
        assert transactions[1].amount == 28511.61
        assert transactions[1].original_comment == "Monthly salary"

        # Check third transaction
        assert transactions[2].date == "2023-08-15"
        assert transactions[2].payee == "Netto"
        assert transactions[2].amount == -45.50

    def test_parse_date_conversion(self):
        """Test date conversion from DD.MM.YYYY to YYYY-MM-DD"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",31.12.2024,Test Payee,,,100.0,,,\n"

        transactions = parser.parse(csv_content)
        assert transactions[0].date == "2024-12-31"

    def test_parse_withdrawal_negative_amount(self):
        """Test that withdrawal amounts become negative"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",01.01.2024,Store,,,250.50,,,\n"

        transactions = parser.parse(csv_content)
        assert transactions[0].amount == -250.50

    def test_parse_deposit_positive_amount(self):
        """Test that deposit amounts remain positive"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",01.01.2024,Salary,,,,5000.00,,\n"

        transactions = parser.parse(csv_content)
        assert transactions[0].amount == 5000.00

    def test_validate_empty_file(self):
        """Test validation of empty file"""
        parser = AceMoneyParser()
        errors = parser.validate(b"")
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_validate_invalid_headers(self):
        """Test validation with invalid headers"""
        parser = AceMoneyParser()
        csv_content = b"wrong,headers,here\n"
        errors = parser.validate(csv_content)
        assert len(errors) == 1
        assert "invalid headers" in errors[0].lower()

    def test_parse_both_amounts_error(self):
        """Test error when both withdrawal and deposit have values"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",01.01.2024,Invalid,,,100.0,200.0,,\n"

        with pytest.raises(ValueError, match="Both withdrawal and deposit"):
            parser.parse(csv_content)

    def test_parse_no_amount_error(self):
        """Test error when neither withdrawal nor deposit have values"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",01.01.2024,Invalid,,,,,,,\n"

        with pytest.raises(ValueError, match="Missing amount"):
            parser.parse(csv_content)

    def test_parse_invalid_date_error(self):
        """Test error with invalid date format"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",2024-01-01,Invalid,,,100.0,,,\n"

        with pytest.raises(ValueError):
            parser.parse(csv_content)

    def test_parse_missing_payee_error(self):
        """Test error when payee is missing"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        csv_content += b",01.01.2024,,,,100.0,,,\n"

        with pytest.raises(ValueError, match="Missing payee"):
            parser.parse(csv_content)

    def test_parse_no_transactions_error(self):
        """Test error when CSV has headers but no data"""
        parser = AceMoneyParser()
        csv_content = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"

        with pytest.raises(ValueError, match="No transactions found"):
            parser.parse(csv_content)

    def test_validate_no_headers_error(self):
        """Test validation when file has no headers"""
        parser = AceMoneyParser()
        errors = parser.validate(b"   \n  \n")
        assert len(errors) > 0


class TestDanskeBankParser:
    """Tests for Danske Bank CSV parser"""

    def test_parse_valid(self):
        """Test parsing a valid Danske Bank CSV"""
        parser = DanskeBankParser()
        transactions = parser.parse(DANSKE_BANK_SAMPLE)

        assert len(transactions) == 3

        # Check first transaction (expense)
        assert transactions[0].date == "2024-11-25"
        assert transactions[0].payee == "Netto ScanNGo"
        assert transactions[0].amount == -41.80
        assert transactions[0].original_category == ""
        assert transactions[0].original_comment == ""

        # Check second transaction
        assert transactions[1].date == "2024-11-25"
        assert transactions[1].payee == "433 Netto Hedehuse"
        assert transactions[1].amount == -609.01

        # Check third transaction (income with thousands separator)
        assert transactions[2].date == "2024-11-26"
        assert transactions[2].payee == "Løn"
        assert transactions[2].amount == 28500.00

    def test_parse_danish_decimals(self):
        """Test parsing Danish decimal format (1.234,56)"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"01.01.2024";"Test";"1.234,56";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        transactions = parser.parse(csv_content)
        assert transactions[0].amount == 1234.56

    def test_parse_negative_amount(self):
        """Test parsing negative amounts"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"01.01.2024";"Test";"-99,99";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        transactions = parser.parse(csv_content)
        assert transactions[0].amount == -99.99

    def test_parse_large_amount_with_thousands(self):
        """Test parsing large amounts with thousand separators"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"01.01.2024";"Test";"123.456,78";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        transactions = parser.parse(csv_content)
        assert transactions[0].amount == 123456.78

    def test_parse_date_conversion(self):
        """Test date conversion from DD.MM.YYYY to YYYY-MM-DD"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"31.12.2024";"Test";"100,00";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        transactions = parser.parse(csv_content)
        assert transactions[0].date == "2024-12-31"

    def test_validate_empty_file(self):
        """Test validation of empty file"""
        parser = DanskeBankParser()
        errors = parser.validate(b"")
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_validate_invalid_headers(self):
        """Test validation with invalid headers"""
        parser = DanskeBankParser()
        csv_content = b'"Wrong";"Headers"\n'
        errors = parser.validate(csv_content)
        assert len(errors) == 1
        assert "invalid headers" in errors[0].lower()

    def test_parse_missing_payee_error(self):
        """Test error when payee is missing"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"01.01.2024";"";"100,00";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        with pytest.raises(ValueError, match="Missing payee"):
            parser.parse(csv_content)

    def test_parse_missing_amount_error(self):
        """Test error when amount is missing"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"01.01.2024";"Test";"";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        with pytest.raises(ValueError, match="Missing amount"):
            parser.parse(csv_content)

    def test_parse_invalid_date_error(self):
        """Test error with invalid date format"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        csv_content += b'"2024-01-01";"Test";"100,00";"0,00";"Udf\xc3\xb8rt";"Nej"\n'

        with pytest.raises(ValueError):
            parser.parse(csv_content)

    def test_parse_no_transactions_error(self):
        """Test error when CSV has headers but no data"""
        parser = DanskeBankParser()
        csv_content = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'

        with pytest.raises(ValueError, match="No transactions found"):
            parser.parse(csv_content)


class TestAutoDetection:
    """Tests for CSV format auto-detection"""

    def test_detect_acemoney_format(self):
        """Test detecting AceMoney format"""
        format_type = detect_csv_format(ACEMONEY_SAMPLE)
        assert format_type == "acemoney"

    def test_detect_danske_bank_format(self):
        """Test detecting Danske Bank format"""
        format_type = detect_csv_format(DANSKE_BANK_SAMPLE)
        assert format_type == "danske_bank"

    def test_detect_empty_file_error(self):
        """Test error when detecting format of empty file"""
        with pytest.raises(ValueError, match="empty"):
            detect_csv_format(b"")

    def test_detect_invalid_format_error(self):
        """Test error when format cannot be detected"""
        csv_content = b"wrong,format,here\ndata,data,data\n"
        with pytest.raises(ValueError, match="Could not detect"):
            detect_csv_format(csv_content)

    def test_get_parser_acemoney(self):
        """Test factory function returns AceMoneyParser"""
        parser = get_parser(ACEMONEY_SAMPLE)
        assert isinstance(parser, AceMoneyParser)

    def test_get_parser_danske_bank(self):
        """Test factory function returns DanskeBankParser"""
        parser = get_parser(DANSKE_BANK_SAMPLE)
        assert isinstance(parser, DanskeBankParser)

    def test_detect_based_on_encoding_and_delimiter(self):
        """Test detection uses both encoding and delimiter"""
        # UTF-8 with semicolon should be Danske Bank
        csv_utf8_semi = b'"Dato";"Tekst";"Bel\xc3\xb8b";"Saldo";"Status";"Afstemt"\n'
        assert detect_csv_format(csv_utf8_semi) == "danske_bank"

        # latin-1 with comma should be AceMoney
        csv_latin_comma = b"transaction,date,payee,category,status,withdrawal,deposit,total,comment\n"
        assert detect_csv_format(csv_latin_comma) == "acemoney"


class TestCSVGenerator:
    """Tests for CSV generator (AceMoney export format)"""

    def test_generate_basic(self):
        """Test generating basic AceMoney CSV"""
        generator = CSVGenerator()
        transactions = [
            {
                'date': '2024-01-15',
                'payee': 'Test Store',
                'amount': -100.50,
                'category': 'Food:Groceries',
                'note': 'Weekly shopping'
            },
            {
                'date': '2024-01-20',
                'payee': 'Salary',
                'amount': 5000.00,
                'category': 'Income:Salary',
                'note': ''
            }
        ]

        csv_bytes = generator.generate(transactions)

        # Decode and check content
        csv_text = csv_bytes.decode('latin-1')
        lines = csv_text.strip().split('\n')

        # Check headers
        assert 'transaction,date,payee,category,status,withdrawal,deposit,total,comment' in lines[0]

        # Check first transaction (expense)
        assert '15.01.2024' in lines[1]  # Date converted
        assert 'Test Store' in lines[1]
        assert '100.50' in lines[1]  # Withdrawal
        assert 'Food:Groceries' in lines[1]
        assert 'Weekly shopping' in lines[1]

        # Check second transaction (income)
        assert '20.01.2024' in lines[2]
        assert 'Salary' in lines[2]
        assert '5000.00' in lines[2]  # Deposit

    def test_generate_date_conversion(self):
        """Test date conversion from YYYY-MM-DD to DD.MM.YYYY"""
        generator = CSVGenerator()
        transactions = [
            {
                'date': '2024-12-31',
                'payee': 'Test',
                'amount': -10.0
            }
        ]

        csv_bytes = generator.generate(transactions)
        csv_text = csv_bytes.decode('latin-1')

        assert '31.12.2024' in csv_text

    def test_generate_amount_splitting(self):
        """Test that negative amounts go to withdrawal, positive to deposit"""
        generator = CSVGenerator()
        transactions = [
            {'date': '2024-01-01', 'payee': 'Expense', 'amount': -50.0},
            {'date': '2024-01-02', 'payee': 'Income', 'amount': 100.0}
        ]

        csv_bytes = generator.generate(transactions)
        csv_text = csv_bytes.decode('latin-1')
        lines = csv_text.strip().split('\n')

        # First transaction: withdrawal column filled, deposit empty
        expense_line = lines[1]
        assert ',50.00,,' in expense_line or ',,50.00,' not in expense_line

        # Second transaction: deposit column filled, withdrawal empty
        income_line = lines[2]
        assert ',100.00,' in income_line

    def test_generate_latin1_encoding(self):
        """Test that output is latin-1 encoded"""
        generator = CSVGenerator()
        transactions = [
            {
                'date': '2024-01-01',
                'payee': 'Løn',  # Danish character
                'amount': 1000.0,
                'category': 'Indkomst',
                'note': 'Månedlig'
            }
        ]

        csv_bytes = generator.generate(transactions)

        # Should be decodable as latin-1
        csv_text = csv_bytes.decode('latin-1')
        assert 'Løn' in csv_text
        assert 'Månedlig' in csv_text

    def test_generate_empty_category_and_note(self):
        """Test generating CSV with missing category and note"""
        generator = CSVGenerator()
        transactions = [
            {
                'date': '2024-01-01',
                'payee': 'Test',
                'amount': -10.0
            }
        ]

        csv_bytes = generator.generate(transactions)
        csv_text = csv_bytes.decode('latin-1')

        # Should not raise error and should have empty fields
        assert 'Test' in csv_text

    def test_generate_preserves_decimal_places(self):
        """Test that amounts are formatted with 2 decimal places"""
        generator = CSVGenerator()
        transactions = [
            {'date': '2024-01-01', 'payee': 'Test', 'amount': -100.5},
            {'date': '2024-01-02', 'payee': 'Test2', 'amount': 50.0}
        ]

        csv_bytes = generator.generate(transactions)
        csv_text = csv_bytes.decode('latin-1')

        assert '100.50' in csv_text
        assert '50.00' in csv_text


class TestParsedTransaction:
    """Tests for ParsedTransaction dataclass"""

    def test_create_transaction(self):
        """Test creating a ParsedTransaction"""
        txn = ParsedTransaction(
            date="2024-01-01",
            payee="Test Payee",
            amount=-100.0,
            original_category="Food",
            original_comment="Test"
        )

        assert txn.date == "2024-01-01"
        assert txn.payee == "Test Payee"
        assert txn.amount == -100.0
        assert txn.original_category == "Food"
        assert txn.original_comment == "Test"

    def test_default_values(self):
        """Test default values for optional fields"""
        txn = ParsedTransaction(
            date="2024-01-01",
            payee="Test",
            amount=50.0
        )

        assert txn.original_category == ""
        assert txn.original_comment == ""


class TestIntegration:
    """Integration tests combining multiple components"""

    def test_parse_and_generate_roundtrip(self):
        """Test parsing CSV and generating it back"""
        # Parse AceMoney CSV
        parser = AceMoneyParser()
        transactions = parser.parse(ACEMONEY_SAMPLE)

        # Convert to dict format for generator
        txn_dicts = [
            {
                'date': t.date,
                'payee': t.payee,
                'amount': t.amount,
                'category': '',
                'note': t.original_comment
            }
            for t in transactions
        ]

        # Generate CSV
        generator = CSVGenerator()
        csv_bytes = generator.generate(txn_dicts)

        # Parse again
        transactions2 = parser.parse(csv_bytes)

        # Should have same data
        assert len(transactions2) == len(transactions)
        for t1, t2 in zip(transactions, transactions2):
            assert t1.date == t2.date
            assert t1.payee == t2.payee
            assert t1.amount == t2.amount

    def test_danske_bank_to_acemoney_conversion(self):
        """Test converting Danske Bank format to AceMoney format"""
        # Parse Danske Bank CSV
        parser = DanskeBankParser()
        transactions = parser.parse(DANSKE_BANK_SAMPLE)

        # Convert to dict format
        txn_dicts = [
            {
                'date': t.date,
                'payee': t.payee,
                'amount': t.amount,
                'category': 'Uncategorized',
                'note': ''
            }
            for t in transactions
        ]

        # Generate AceMoney CSV
        generator = CSVGenerator()
        csv_bytes = generator.generate(txn_dicts)

        # Parse with AceMoney parser
        acemoney_parser = AceMoneyParser()
        transactions2 = acemoney_parser.parse(csv_bytes)

        # Should have same core data
        assert len(transactions2) == len(transactions)
        for t1, t2 in zip(transactions, transactions2):
            assert t1.date == t2.date
            assert t1.payee == t2.payee
            assert abs(t1.amount - t2.amount) < 0.01  # Float comparison

    def test_auto_detect_and_parse(self):
        """Test auto-detection followed by parsing"""
        # Test with AceMoney
        parser = get_parser(ACEMONEY_SAMPLE)
        transactions = parser.parse(ACEMONEY_SAMPLE)
        assert len(transactions) == 3

        # Test with Danske Bank
        parser = get_parser(DANSKE_BANK_SAMPLE)
        transactions = parser.parse(DANSKE_BANK_SAMPLE)
        assert len(transactions) == 3
