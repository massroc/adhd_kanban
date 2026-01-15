/**
 * Unit tests for offline.js
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    getIsOffline,
    setOfflineMode,
    onOfflineChange,
    cacheBoard,
    getCachedBoard,
    clearBoardCache,
    getCacheTimestamp,
    initOfflineDetection
} from '../../src/js/offline.js';

describe('Offline State Management', () => {
    beforeEach(() => {
        // Reset offline state by setting it to false
        setOfflineMode(false);
    });

    it('getIsOffline returns false by default', () => {
        expect(getIsOffline()).toBe(false);
    });

    it('setOfflineMode changes offline state to true', () => {
        setOfflineMode(true);
        expect(getIsOffline()).toBe(true);
    });

    it('setOfflineMode changes offline state to false', () => {
        setOfflineMode(true);
        setOfflineMode(false);
        expect(getIsOffline()).toBe(false);
    });

    it('onOfflineChange notifies listener when state changes', () => {
        const listener = vi.fn();
        onOfflineChange(listener);

        setOfflineMode(true);

        expect(listener).toHaveBeenCalledWith(true);
    });

    it('onOfflineChange does not notify when state is same', () => {
        const listener = vi.fn();
        setOfflineMode(false); // Ensure starting state
        onOfflineChange(listener);
        listener.mockClear(); // Clear any initial calls

        setOfflineMode(false); // Same state

        expect(listener).not.toHaveBeenCalled();
    });

    it('onOfflineChange unsubscribe function works', () => {
        const listener = vi.fn();
        const unsubscribe = onOfflineChange(listener);

        unsubscribe();
        setOfflineMode(true);

        expect(listener).not.toHaveBeenCalled();
    });

    it('multiple listeners are all notified', () => {
        const listener1 = vi.fn();
        const listener2 = vi.fn();

        onOfflineChange(listener1);
        onOfflineChange(listener2);

        setOfflineMode(true);

        expect(listener1).toHaveBeenCalledWith(true);
        expect(listener2).toHaveBeenCalledWith(true);
    });
});

describe('Board Cache Operations', () => {
    const mockBoardData = {
        columns: [
            { id: 1, name: 'To Do', order: 1, tasks: [] },
            { id: 2, name: 'Done', order: 2, tasks: [{ id: 1, title: 'Test task' }] }
        ]
    };

    beforeEach(() => {
        clearBoardCache();
    });

    it('cacheBoard stores data in localStorage', () => {
        cacheBoard(mockBoardData);

        expect(localStorage.setItem).toHaveBeenCalledWith(
            'board_cache',
            JSON.stringify(mockBoardData)
        );
    });

    it('cacheBoard stores timestamp', () => {
        const beforeTime = Date.now();
        cacheBoard(mockBoardData);
        const afterTime = Date.now();

        const timestamp = getCacheTimestamp();
        expect(timestamp).toBeGreaterThanOrEqual(beforeTime);
        expect(timestamp).toBeLessThanOrEqual(afterTime);
    });

    it('getCachedBoard returns null when no cache exists', () => {
        expect(getCachedBoard()).toBeNull();
    });

    it('getCachedBoard retrieves cached data', () => {
        localStorage.setItem('board_cache', JSON.stringify(mockBoardData));

        const cached = getCachedBoard();

        expect(cached).toEqual(mockBoardData);
    });

    it('clearBoardCache removes cached data', () => {
        cacheBoard(mockBoardData);
        clearBoardCache();

        expect(localStorage.removeItem).toHaveBeenCalledWith('board_cache');
        expect(localStorage.removeItem).toHaveBeenCalledWith('board_cache_timestamp');
    });

    it('getCacheTimestamp returns null when no cache exists', () => {
        expect(getCacheTimestamp()).toBeNull();
    });

    it('cacheBoard handles localStorage errors gracefully', () => {
        const originalSetItem = localStorage.setItem;
        localStorage.setItem = vi.fn(() => {
            throw new Error('QuotaExceededError');
        });

        // Should not throw
        expect(() => cacheBoard(mockBoardData)).not.toThrow();

        localStorage.setItem = originalSetItem;
    });

    it('getCachedBoard handles invalid JSON gracefully', () => {
        localStorage.getItem.mockReturnValueOnce('invalid json {{{');

        // Should not throw, returns null
        expect(getCachedBoard()).toBeNull();
    });
});

describe('Offline Detection Initialization', () => {
    let addEventListenerSpy;

    beforeEach(() => {
        addEventListenerSpy = vi.spyOn(window, 'addEventListener');
        setOfflineMode(false);
    });

    it('initOfflineDetection sets up online event listener', () => {
        initOfflineDetection();

        expect(addEventListenerSpy).toHaveBeenCalledWith(
            'online',
            expect.any(Function)
        );
    });

    it('initOfflineDetection sets up offline event listener', () => {
        initOfflineDetection();

        expect(addEventListenerSpy).toHaveBeenCalledWith(
            'offline',
            expect.any(Function)
        );
    });

    it('initOfflineDetection sets initial state based on navigator.onLine', () => {
        // Mock navigator.onLine as false
        Object.defineProperty(navigator, 'onLine', {
            value: false,
            configurable: true
        });

        initOfflineDetection();

        expect(getIsOffline()).toBe(true);

        // Restore
        Object.defineProperty(navigator, 'onLine', {
            value: true,
            configurable: true
        });
    });
});
