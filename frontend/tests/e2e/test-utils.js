/**
 * E2E Test Utilities
 * Provides helper functions for test user management and common operations
 */

const API_BASE = process.env.TEST_API_BASE || 'http://localhost:8000/api/v1';

/**
 * Create a test user via the API, or return existing user's token
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{token: string, user: object}>}
 */
export async function createTestUser(username, password) {
    // Try to register first
    const registerResponse = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username,
            password,
            password_confirm: password
        })
    });

    if (registerResponse.ok) {
        const data = await registerResponse.json();
        console.log(`Created test user: ${username}`);
        return data;
    }

    // User might already exist - try logging in
    if (registerResponse.status === 400) {
        const loginResponse = await fetch(`${API_BASE}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (loginResponse.ok) {
            const data = await loginResponse.json();
            console.log(`Logged in existing test user: ${username}`);
            return data;
        }
    }

    const error = await registerResponse.text();
    throw new Error(`Failed to create/login test user: ${registerResponse.status} - ${error}`);
}

/**
 * Generate a unique username for tests
 * @returns {string}
 */
export function generateUniqueUsername() {
    return `e2e_test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Default test credentials
 */
export const TEST_USER = {
    username: process.env.TEST_USERNAME || 'e2e_test_user',
    password: process.env.TEST_PASSWORD || 'e2e_test_password_123',
};

/**
 * Login helper for Playwright tests
 * @param {import('@playwright/test').Page} page
 * @param {string} username
 * @param {string} password
 */
export async function loginUser(page, username = TEST_USER.username, password = TEST_USER.password) {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.fill('#login-username', username);
    await page.fill('#login-password', password);
    await page.click('#login-submit');
    // Wait for redirect to board (supports both /board.html and /board clean URL)
    await page.waitForURL(/board(\.html)?$/, { timeout: 15000 });
}
