// Offline mode management module
// Handles caching board state and detecting online/offline status

const CACHE_KEY = 'board_cache';
const CACHE_TIMESTAMP_KEY = 'board_cache_timestamp';

let isOfflineMode = false;
let offlineListeners = [];

// State management
export function getIsOffline() {
    return isOfflineMode;
}

export function setOfflineMode(offline) {
    if (isOfflineMode !== offline) {
        isOfflineMode = offline;
        notifyListeners();
    }
}

export function onOfflineChange(callback) {
    offlineListeners.push(callback);
    // Return unsubscribe function
    return () => {
        offlineListeners = offlineListeners.filter(cb => cb !== callback);
    };
}

function notifyListeners() {
    offlineListeners.forEach(cb => cb(isOfflineMode));
}

// Cache operations
export function cacheBoard(boardData) {
    try {
        localStorage.setItem(CACHE_KEY, JSON.stringify(boardData));
        localStorage.setItem(CACHE_TIMESTAMP_KEY, Date.now().toString());
    } catch (e) {
        console.warn('Failed to cache board:', e);
    }
}

export function getCachedBoard() {
    try {
        const data = localStorage.getItem(CACHE_KEY);
        return data ? JSON.parse(data) : null;
    } catch (e) {
        console.warn('Failed to read board cache:', e);
        return null;
    }
}

export function clearBoardCache() {
    localStorage.removeItem(CACHE_KEY);
    localStorage.removeItem(CACHE_TIMESTAMP_KEY);
}

export function getCacheTimestamp() {
    const ts = localStorage.getItem(CACHE_TIMESTAMP_KEY);
    return ts ? parseInt(ts, 10) : null;
}

// Initialize connectivity listeners
export function initOfflineDetection() {
    window.addEventListener('online', () => setOfflineMode(false));
    window.addEventListener('offline', () => setOfflineMode(true));

    // Set initial state based on navigator
    setOfflineMode(!navigator.onLine);
}
