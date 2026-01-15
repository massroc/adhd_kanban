/**
 * Playwright Global Setup
 * Ensures test user exists before running E2E tests
 */

import { createTestUser, TEST_USER } from './test-utils.js';

export default async function globalSetup() {
    console.log('\n[Global Setup] Preparing E2E test environment...');

    // Check backend availability first
    console.log('[Global Setup] Checking backend availability...');
    try {
        const healthResponse = await fetch('http://localhost:8000/api/v1/health/', {
            signal: AbortSignal.timeout(5000)
        });
        if (!healthResponse.ok) {
            throw new Error(`Backend returned ${healthResponse.status}`);
        }
        console.log('[Global Setup] Backend is available');
    } catch (error) {
        console.error('\n[Global Setup] ERROR: Backend is not available at http://localhost:8000');
        console.error('[Global Setup] Please start the backend before running E2E tests:');
        console.error('[Global Setup]   cd backend && docker-compose up -d');
        console.error('[Global Setup]   python manage.py runserver');
        console.error(`[Global Setup] Error: ${error.message}\n`);
        process.exit(1);
    }

    try {
        const result = await createTestUser(TEST_USER.username, TEST_USER.password);
        console.log(`[Global Setup] Test user ready: ${TEST_USER.username}`);
        console.log(`[Global Setup] Token available for tests`);

        // Store token in environment for potential use in tests
        process.env.TEST_USER_TOKEN = result.token;
    } catch (error) {
        console.warn(`[Global Setup] Warning: Could not create test user: ${error.message}`);
        console.warn('[Global Setup] E2E tests requiring authentication may fail');
    }

    console.log('[Global Setup] Complete\n');
}
