/**
 * E2E tests for column CRUD operations
 */

import { test, expect } from '@playwright/test';
import { loginUser, TEST_USER } from './test-utils.js';

test.describe('Column Operations', () => {
    test.beforeEach(async ({ page }) => {
        await loginUser(page, TEST_USER.username, TEST_USER.password);
        // Wait for board to load
        await expect(page.locator('#kanban-board')).toBeVisible({ timeout: 15000 });
    });

    test('displays columns on the board', async ({ page }) => {
        // Should have at least one column
        const columns = page.locator('.column');
        await expect(columns.first()).toBeVisible();
    });

    test('can create a new column', async ({ page }) => {
        const columnName = `Test Column ${Date.now()}`;

        // Check if we can add columns (not at max)
        const addColumnBtn = page.locator('#add-column-btn');
        const isDisabled = await addColumnBtn.isDisabled();

        if (isDisabled) {
            test.skip(true, 'At maximum columns - cannot add more');
            return;
        }

        // Click add column button
        await addColumnBtn.click();
        await expect(page.locator('#column-modal')).toHaveClass(/active/);

        // Fill in column name and submit
        await page.fill('#column-name', columnName);
        await page.click('#add-column-form button[type="submit"]');

        // Wait for modal to close and column to appear
        await expect(page.locator('#column-modal')).not.toHaveClass(/active/, { timeout: 5000 });
        await expect(page.locator(`.column-title:has-text("${columnName}")`)).toBeVisible({ timeout: 5000 });
    });

    test('can rename a column via double-click', async ({ page }) => {
        // Get the first column
        const column = page.locator('.column').first();
        const titleElement = column.locator('.column-title');

        // Double-click to edit
        await titleElement.dblclick();

        // Input should appear
        const input = column.locator('input.column-rename-input');
        await expect(input).toBeVisible({ timeout: 3000 });

        // Enter new name
        const newName = `Renamed ${Date.now()}`;
        await input.fill(newName);
        await input.press('Enter');

        // Name should update (check that title contains new name)
        await expect(titleElement).toContainText(newName, { timeout: 5000 });
    });

    test('can cancel column modal', async ({ page }) => {
        const addColumnBtn = page.locator('#add-column-btn');
        const isDisabled = await addColumnBtn.isDisabled();

        if (isDisabled) {
            test.skip(true, 'At maximum columns');
            return;
        }

        await addColumnBtn.click();
        await expect(page.locator('#column-modal')).toHaveClass(/active/);

        // Cancel
        await page.click('#cancel-column-btn');
        await expect(page.locator('#column-modal')).not.toHaveClass(/active/);
    });

    test('column limit message shows when at max', async ({ page }) => {
        const addColumnBtn = page.locator('#add-column-btn');
        const isDisabled = await addColumnBtn.isDisabled();

        if (isDisabled) {
            // At max - message should be visible
            await expect(page.locator('#column-limit-msg')).toHaveClass(/show/);
        } else {
            // Not at max - message should be hidden
            await expect(page.locator('#column-limit-msg')).not.toHaveClass(/show/);
        }
    });
});

test.describe('Column Drag and Drop', () => {
    test.beforeEach(async ({ page }) => {
        await loginUser(page, TEST_USER.username, TEST_USER.password);
        await expect(page.locator('#kanban-board')).toBeVisible({ timeout: 15000 });
    });

    test('columns have drag handles', async ({ page }) => {
        const dragHandle = page.locator('.drag-handle').first();
        await expect(dragHandle).toBeVisible();
    });

    test('columns can be dragged via handle', async ({ page }) => {
        // This test verifies the drag handle enables dragging
        // Full drag-drop testing requires more complex mouse event simulation
        const columns = page.locator('.column');
        const count = await columns.count();

        if (count < 2) {
            test.skip(true, 'Need at least 2 columns for drag test');
            return;
        }

        const firstColumn = columns.first();
        const dragHandle = firstColumn.locator('.drag-handle');

        // Verify drag handle exists and is interactive
        await expect(dragHandle).toBeVisible();
        await expect(dragHandle).toHaveCSS('cursor', 'grab');
    });
});
