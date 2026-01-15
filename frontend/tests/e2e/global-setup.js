/**
 * Playwright Global Setup
 * Ensures test user exists and cleans up stale test data before running E2E tests
 */

import { createTestUser, cleanupTestData, TEST_USER } from './test-utils.js';

export default async function globalSetup() {
    console.log('\n[Global Setup] Preparing E2E test environment...');

    // Backend availability is now managed by Playwright webServer config
    try {
        const result = await createTestUser(TEST_USER.username, TEST_USER.password);
        console.log(`[Global Setup] Test user ready: ${TEST_USER.username}`);

        // Store token in environment for potential use in tests
        process.env.TEST_USER_TOKEN = result.token;

        // Clean up any stale test data from previous runs
        console.log('[Global Setup] Cleaning up stale test data...');
        await cleanupTestData(result.token);
    } catch (error) {
        console.warn(`[Global Setup] Warning: Could not create test user: ${error.message}`);
        console.warn('[Global Setup] E2E tests requiring authentication may fail');
    }

    console.log('[Global Setup] Complete\n');
}
