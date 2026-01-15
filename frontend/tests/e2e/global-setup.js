/**
 * Playwright Global Setup
 * Ensures test user exists before running E2E tests
 */

import { createTestUser, TEST_USER } from './test-utils.js';

export default async function globalSetup() {
    console.log('\n[Global Setup] Preparing E2E test environment...');

    try {
        const result = await createTestUser(TEST_USER.username, TEST_USER.password);
        console.log(`[Global Setup] Test user ready: ${TEST_USER.username}`);
        console.log(`[Global Setup] Token available for tests`);

        // Store token in environment for potential use in tests
        process.env.TEST_USER_TOKEN = result.token;
    } catch (error) {
        console.warn(`[Global Setup] Warning: Could not create test user: ${error.message}`);
        console.warn('[Global Setup] E2E tests requiring authentication may fail');
        console.warn('[Global Setup] Make sure the backend is running at http://localhost:8000');
    }

    console.log('[Global Setup] Complete\n');
}
