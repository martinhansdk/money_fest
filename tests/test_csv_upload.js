/**
 * Integration test for CSV upload functionality
 * Tests both AceMoney and Danske Bank CSV formats
 */

const { chromium } = require('playwright');
const path = require('path');

const BASE_URL = process.env.BASE_URL || 'http://localhost:1111';
const USERNAME = 'test';
const PASSWORD = 'test1234';

async function runTests() {
    const browser = await chromium.launch({
        headless: process.env.HEADLESS !== 'false'
    });
    const page = await browser.newPage();

    let testsPassed = 0;
    let testsFailed = 0;

    try {
        // Test 1: Login
        console.log('Test 1: Login with test user');
        await page.goto(`${BASE_URL}/static/index.html`);
        await page.fill('input[name="username"]', USERNAME);
        await page.fill('input[name="password"]', PASSWORD);
        await page.click('button[type="submit"]');
        await page.waitForURL('**/batches.html', { timeout: 5000 });
        console.log('✓ Test 1 passed: Successfully logged in');
        testsPassed++;

        // Test 2: Upload AceMoney CSV
        console.log('\nTest 2: Upload AceMoney CSV (DD-MM-YYYY format)');
        await page.click('button:has-text("Upload CSV")');
        await page.waitForSelector('#uploadModal.visible');
        await page.fill('#batchName', 'AceMoney Test Batch');

        const aceMoneyFile = path.join(__dirname, '..', 'acemoney_example.csv');
        await page.setInputFiles('#csvFile', aceMoneyFile);

        await page.click('button[type="submit"]');

        // Wait for either error or redirect
        const result = await Promise.race([
            page.waitForURL('**/categorize.html*', { timeout: 5000 })
                .then(() => ({ success: true }))
                .catch(() => ({ success: false })),
            page.waitForSelector('#uploadError:visible', { timeout: 5000 })
                .then(() => ({ success: false, error: true }))
                .catch(() => ({ success: false }))
        ]);

        if (result.error) {
            const errorText = await page.locator('#uploadError').textContent();
            console.log(`✗ Test 2 failed: ${errorText}`);
            testsFailed++;
        } else if (result.success) {
            console.log('✓ Test 2 passed: AceMoney CSV uploaded successfully');
            testsPassed++;

            // Verify we're on the categorization page
            const url = page.url();
            console.log(`  Redirected to: ${url}`);
        } else {
            console.log('✗ Test 2 failed: Unknown error (timeout or no response)');
            testsFailed++;
        }

        // Go back to batches page
        await page.goto(`${BASE_URL}/static/batches.html`);
        await page.waitForTimeout(1000);

        // Test 3: Upload Danske Bank CSV
        console.log('\nTest 3: Upload Danske Bank CSV (semicolon-delimited)');
        await page.click('button:has-text("Upload CSV")');
        await page.waitForSelector('#uploadModal.visible');
        await page.fill('#batchName', 'Danske Bank Test Batch');

        const danskeBankFile = path.join(__dirname, '..', 'danske_bank_example.csv');
        await page.setInputFiles('#csvFile', danskeBankFile);

        await page.click('button[type="submit"]');

        // Wait for either error or redirect
        const result2 = await Promise.race([
            page.waitForURL('**/categorize.html*', { timeout: 5000 })
                .then(() => ({ success: true }))
                .catch(() => ({ success: false })),
            page.waitForSelector('#uploadError:visible', { timeout: 5000 })
                .then(() => ({ success: false, error: true }))
                .catch(() => ({ success: false }))
        ]);

        if (result2.error) {
            const errorText = await page.locator('#uploadError').textContent();
            console.log(`✗ Test 3 failed: ${errorText}`);
            testsFailed++;
        } else if (result2.success) {
            console.log('✓ Test 3 passed: Danske Bank CSV uploaded successfully');
            testsPassed++;

            // Verify we're on the categorization page
            const url = page.url();
            console.log(`  Redirected to: ${url}`);
        } else {
            console.log('✗ Test 3 failed: Unknown error (timeout or no response)');
            testsFailed++;
        }

    } catch (error) {
        console.error('Test suite error:', error.message);
        testsFailed++;
    } finally {
        await browser.close();
    }

    // Print summary
    console.log('\n' + '='.repeat(50));
    console.log('Test Summary:');
    console.log(`  Passed: ${testsPassed}`);
    console.log(`  Failed: ${testsFailed}`);
    console.log(`  Total:  ${testsPassed + testsFailed}`);
    console.log('='.repeat(50));

    // Exit with appropriate code
    process.exit(testsFailed > 0 ? 1 : 0);
}

// Run tests
runTests();
