/**
 * CSV Upload Tests
 *
 * Tests various CSV upload scenarios including:
 * - Different date formats (YYYY/MM/DD, DD.MM.YYYY, DD-MM-YYYY, YYYY-MM-DD)
 * - Header aliases ("Num" for "transaction", "S" for "status")
 * - Empty amount rows (should be skipped)
 * - Both withdrawals and deposits
 */

const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('CSV Upload', () => {
    let page;

    test.beforeEach(async ({ browser }) => {
        page = await browser.newPage();
        await page.goto('http://localhost:1111/static/index.html');

        // Login as alice
        await page.fill('input[type="text"]', 'alice');
        await page.fill('input[type="password"]', 'password123');
        await page.click('button:has-text("Login")');

        // Wait for batches page to load
        await page.waitForURL('**/batches.html');
        await expect(page.locator('h1')).toHaveText('Batches');
    });

    test.afterEach(async () => {
        await page.close();
    });

    test('should upload AceMoney CSV with multiple date formats and header aliases', async () => {
        // Click Upload CSV button
        await page.click('button:has-text("Upload CSV")');

        // Wait for modal to appear
        await expect(page.locator('.modal-content')).toBeVisible();

        // Fill in batch name
        await page.fill('input[placeholder*="November"]', 'Test CSV Upload');

        // Upload the test file
        const filePath = path.join(__dirname, 'fixtures', 'test_acemoney.csv');
        const fileInput = await page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);

        // Wait for upload request to complete
        const uploadPromise = page.waitForResponse(
            response => response.url().includes('/batches') && response.request().method() === 'POST',
            { timeout: 10000 }
        );

        // Click Upload button
        await page.click('button:has-text("Upload"):not(:has-text("CSV"))');

        // Wait for upload response
        const response = await uploadPromise;
        expect(response.status()).toBe(201);

        // Wait for navigation to categorize page
        await page.waitForURL('**/categorize.html**', { timeout: 5000 });

        // Navigate back to batches page
        await page.goto('http://localhost:1111/static/batches.html');
        await page.waitForLoadState('networkidle');

        // Verify the batch was created
        // Should have 9 transactions (10 rows in CSV, but 1 has no amount and should be skipped)
        const batchCard = page.locator('.batch-card').filter({ hasText: 'Test CSV Upload' }).first();
        await expect(batchCard).toBeVisible({ timeout: 5000 });

        // Check transaction count
        await expect(batchCard).toContainText('0/9 categorized');

        // Check date range
        await expect(batchCard).toContainText('2005-02-01 to 2005-02-10');

        // Check status
        await expect(batchCard).toContainText('In Progress');
    });

    test('should handle CSV with mixed date formats correctly', async () => {
        // Upload the test file
        await page.click('button:has-text("Upload CSV")');
        await page.fill('input[placeholder*="November"]', 'Date Format Test');

        const filePath = path.join(__dirname, 'fixtures', 'test_acemoney.csv');
        const fileInput = await page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);

        const uploadPromise = page.waitForResponse(
            response => response.url().includes('/batches') && response.request().method() === 'POST',
            { timeout: 10000 }
        );

        await page.click('button:has-text("Upload"):not(:has-text("CSV"))');

        const response = await uploadPromise;
        expect(response.status()).toBe(201);

        // Wait for navigation to categorize page (happens automatically)
        await page.waitForURL('**/categorize.html**', { timeout: 5000 });

        // Verify transactions are parsed correctly
        // Check that we have exactly 9 transactions (1 was skipped due to empty amount)
        const transactionRows = page.locator('tbody tr');
        await expect(transactionRows).toHaveCount(9);

        // Verify specific dates are parsed correctly from different formats
        // All should be displayed in the same format (e.g., "Feb 1, 2005")
        await expect(page.locator('td:has-text("Feb 1, 2005")')).toHaveCount(1);
        await expect(page.locator('td:has-text("Feb 2, 2005")')).toHaveCount(1);
        await expect(page.locator('td:has-text("Feb 3, 2005")')).toHaveCount(1);
        await expect(page.locator('td:has-text("Feb 4, 2005")')).toHaveCount(1);
        await expect(page.locator('td:has-text("Feb 5, 2005")')).toHaveCount(1);
    });

    test('should skip rows with no amount (memo entries)', async () => {
        // Upload the test file
        await page.click('button:has-text("Upload CSV")');
        await page.fill('input[placeholder*="November"]', 'Memo Entry Test');

        const filePath = path.join(__dirname, 'fixtures', 'test_acemoney.csv');
        const fileInput = await page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);

        const uploadPromise = page.waitForResponse(
            response => response.url().includes('/batches') && response.request().method() === 'POST'
        );

        await page.click('button:has-text("Upload"):not(:has-text("CSV"))');

        const response = await uploadPromise;
        expect(response.status()).toBe(201);

        // Wait for navigation to categorize page (happens automatically)
        await page.waitForURL('**/categorize.html**', { timeout: 5000 });

        // Verify memo entry is NOT present (should be skipped)
        await expect(page.locator('td:has-text("Memo Entry")')).not.toBeVisible();
        await expect(page.locator('td:has-text("Balance check")')).not.toBeVisible();

        // Verify we have 9 transactions (not 10)
        const transactionRows = page.locator('tbody tr');
        await expect(transactionRows).toHaveCount(9);
    });

    test('should parse withdrawals and deposits correctly', async () => {
        // Upload the test file
        await page.click('button:has-text("Upload CSV")');
        await page.fill('input[placeholder*="November"]', 'Amount Test');

        const filePath = path.join(__dirname, 'fixtures', 'test_acemoney.csv');
        const fileInput = await page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);

        const uploadPromise = page.waitForResponse(
            response => response.url().includes('/batches') && response.request().method() === 'POST'
        );

        await page.click('button:has-text("Upload"):not(:has-text("CSV"))');

        const response = await uploadPromise;
        expect(response.status()).toBe(201);

        // Wait for navigation to categorize page (happens automatically)
        await page.waitForURL('**/categorize.html**', { timeout: 5000 });

        // Check withdrawals (expenses) - should be negative
        const groceryRow = page.locator('tr:has-text("Grocery Store A")');
        await expect(groceryRow).toContainText('-125.50');

        // Check deposits (income) - should be positive (no minus sign)
        const salaryRow = page.locator('tr:has-text("Employer XYZ")');
        await expect(salaryRow).toContainText('2500.00');
        // Get the amount cell (4th column) and verify it's positive
        const amountCell = salaryRow.locator('td').nth(3);
        const amountText = await amountCell.textContent();
        expect(amountText).not.toContain('-');
        expect(amountText).toContain('2500.00');
    });

    test('should import transactions without categories', async () => {
        // Upload the test file
        await page.click('button:has-text("Upload CSV")');
        await page.fill('input[placeholder*="November"]', 'Category Test');

        const filePath = path.join(__dirname, 'fixtures', 'test_acemoney.csv');
        const fileInput = await page.locator('input[type="file"]');
        await fileInput.setInputFiles(filePath);

        const uploadPromise = page.waitForResponse(
            response => response.url().includes('/batches') && response.request().method() === 'POST'
        );

        await page.click('button:has-text("Upload"):not(:has-text("CSV"))');

        const response = await uploadPromise;
        expect(response.status()).toBe(201);

        // Wait for navigation to categorize page (happens automatically)
        await page.waitForURL('**/categorize.html**', { timeout: 5000 });

        // Verify transactions are imported without categories (all uncategorized)
        // Switch to "Uncategorized" filter
        await page.click('button:has-text("Uncategorized")');

        // All 9 transactions should be visible (all uncategorized)
        const transactionRows = page.locator('tbody tr');
        await expect(transactionRows).toHaveCount(9);
    });
});
