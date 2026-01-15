import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { showToast, showError, showSuccess, showWarning, showInfo, dismissToast } from '../../src/js/toast.js';

describe('Toast Notifications', () => {
    beforeEach(() => {
        // Clean up any existing toasts
        const container = document.getElementById('toast-container');
        if (container) container.remove();
    });

    afterEach(() => {
        const container = document.getElementById('toast-container');
        if (container) container.remove();
    });

    describe('showToast', () => {
        it('creates toast container on first toast', () => {
            showToast('Test message');
            expect(document.getElementById('toast-container')).not.toBeNull();
        });

        it('reuses existing toast container', () => {
            showToast('First message');
            showToast('Second message');
            const containers = document.querySelectorAll('#toast-container');
            expect(containers.length).toBe(1);
        });

        it('creates toast with correct type class', () => {
            showToast('Error message', { type: 'error' });
            const toast = document.querySelector('.toast-error');
            expect(toast).not.toBeNull();
        });

        it('shows toast message', () => {
            showToast('Hello World');
            const message = document.querySelector('.toast-message');
            expect(message.textContent).toBe('Hello World');
        });

        it('escapes HTML in messages to prevent XSS', () => {
            showToast('<script>alert("xss")</script>');
            const message = document.querySelector('.toast-message');
            expect(message.innerHTML).not.toContain('<script>');
            expect(message.textContent).toContain('<script>');
        });

        it('includes close button when dismissible', () => {
            showToast('Test', { dismissible: true });
            const closeBtn = document.querySelector('.toast-close');
            expect(closeBtn).not.toBeNull();
        });

        it('excludes close button when not dismissible', () => {
            showToast('Test', { dismissible: false });
            const closeBtn = document.querySelector('.toast-close');
            expect(closeBtn).toBeNull();
        });

        it('adds toast-show class for animation', async () => {
            showToast('Test');
            // Wait for requestAnimationFrame
            await new Promise(resolve => requestAnimationFrame(resolve));
            const toast = document.querySelector('.toast');
            expect(toast.classList.contains('toast-show')).toBe(true);
        });

        it('auto-dismisses after duration', async () => {
            vi.useFakeTimers();
            showToast('Test', { duration: 1000 });

            expect(document.querySelector('.toast')).not.toBeNull();

            vi.advanceTimersByTime(1500);
            // Toast should have hide class
            const toast = document.querySelector('.toast');
            expect(toast.classList.contains('toast-hide')).toBe(true);

            vi.useRealTimers();
        });

        it('can be manually dismissed via close button', async () => {
            vi.useFakeTimers();
            showToast('Test', { duration: 0 }); // No auto-dismiss

            const closeBtn = document.querySelector('.toast-close');
            closeBtn.click();

            const toast = document.querySelector('.toast');
            expect(toast.classList.contains('toast-hide')).toBe(true);

            vi.useRealTimers();
        });
    });

    describe('convenience methods', () => {
        it('showSuccess creates success toast', () => {
            showSuccess('Success message');
            expect(document.querySelector('.toast-success')).not.toBeNull();
        });

        it('showError creates error toast', () => {
            showError('Error message');
            expect(document.querySelector('.toast-error')).not.toBeNull();
        });

        it('showWarning creates warning toast', () => {
            showWarning('Warning message');
            expect(document.querySelector('.toast-warning')).not.toBeNull();
        });

        it('showInfo creates info toast', () => {
            showInfo('Info message');
            expect(document.querySelector('.toast-info')).not.toBeNull();
        });

        it('showError has longer default duration', () => {
            vi.useFakeTimers();
            showError('Error');

            // Advance past default duration (4000ms) but before error duration (6000ms)
            vi.advanceTimersByTime(5000);
            const toast = document.querySelector('.toast');
            expect(toast.classList.contains('toast-hide')).toBe(false);

            // Now advance past error duration
            vi.advanceTimersByTime(2000);
            expect(toast.classList.contains('toast-hide')).toBe(true);

            vi.useRealTimers();
        });
    });

    describe('accessibility', () => {
        it('toast container has role="alert"', () => {
            showToast('Test');
            const container = document.getElementById('toast-container');
            expect(container.getAttribute('role')).toBe('alert');
        });

        it('toast container has aria-live="polite"', () => {
            showToast('Test');
            const container = document.getElementById('toast-container');
            expect(container.getAttribute('aria-live')).toBe('polite');
        });

        it('close button has aria-label', () => {
            showToast('Test');
            const closeBtn = document.querySelector('.toast-close');
            expect(closeBtn.getAttribute('aria-label')).toBe('Dismiss');
        });
    });

    describe('icons', () => {
        it('success toast has checkmark icon', () => {
            showSuccess('Test');
            const icon = document.querySelector('.toast-icon');
            expect(icon.textContent).toBe('\u2713');
        });

        it('error toast has X icon', () => {
            showError('Test');
            const icon = document.querySelector('.toast-icon');
            expect(icon.textContent).toBe('\u2717');
        });

        it('warning toast has warning icon', () => {
            showWarning('Test');
            const icon = document.querySelector('.toast-icon');
            expect(icon.textContent).toBe('\u26A0');
        });

        it('info toast has info icon', () => {
            showInfo('Test');
            const icon = document.querySelector('.toast-icon');
            expect(icon.textContent).toBe('\u2139');
        });
    });
});
