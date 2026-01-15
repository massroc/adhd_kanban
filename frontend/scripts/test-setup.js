#!/usr/bin/env node
/**
 * E2E Test Setup Script
 * Starts database and backend before running E2E tests
 */

import { spawn, execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backendDir = path.join(__dirname, '..', '..', 'backend');
const projectRoot = path.join(__dirname, '..', '..');

// Detect platform and set Python path
const isWindows = process.platform === 'win32';
const venvPython = isWindows
    ? path.join(projectRoot, 'venv', 'Scripts', 'python.exe')
    : path.join(projectRoot, 'venv', 'bin', 'python');

const BACKEND_URL = 'http://localhost:8000/api/v1/health/';
const MAX_WAIT_SECONDS = 30;

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function isBackendRunning() {
    try {
        const response = await fetch(BACKEND_URL, {
            signal: AbortSignal.timeout(2000)
        });
        return response.ok;
    } catch {
        return false;
    }
}

async function waitForBackend() {
    console.log('[Setup] Waiting for backend to be ready...');
    for (let i = 0; i < MAX_WAIT_SECONDS; i++) {
        if (await isBackendRunning()) {
            console.log('[Setup] Backend is ready!');
            return true;
        }
        await sleep(1000);
    }
    throw new Error(`Backend not ready after ${MAX_WAIT_SECONDS} seconds`);
}

async function main() {
    console.log('[Setup] E2E Test Environment Setup');
    console.log('[Setup] ================================\n');

    // Check if backend is already running
    if (await isBackendRunning()) {
        console.log('[Setup] Backend is already running, skipping setup');
        return;
    }

    // Start PostgreSQL
    console.log('[Setup] Starting PostgreSQL via docker-compose...');
    try {
        execSync('docker-compose up -d', {
            cwd: backendDir,
            stdio: 'inherit'
        });
    } catch (error) {
        console.error('[Setup] Failed to start PostgreSQL:', error.message);
        console.error('[Setup] Make sure Docker is running');
        process.exit(1);
    }

    // Wait for database to be ready
    console.log('[Setup] Waiting for database to initialize...');
    await sleep(3000);

    // Start Django backend
    console.log('[Setup] Starting Django backend...');
    console.log(`[Setup] Using Python: ${venvPython}`);

    const backend = spawn(venvPython, ['manage.py', 'runserver', '0.0.0.0:8000'], {
        cwd: backendDir,
        stdio: 'inherit',
        detached: !isWindows,  // detached doesn't work well on Windows
        shell: isWindows
    });

    backend.unref();

    // Wait for backend to be ready
    try {
        await waitForBackend();
    } catch (error) {
        console.error(`[Setup] ${error.message}`);
        console.error('[Setup] Check that:');
        console.error('[Setup]   1. Python venv exists at project root');
        console.error('[Setup]   2. Django dependencies are installed');
        console.error('[Setup]   3. Database migrations are up to date');
        process.exit(1);
    }

    console.log('\n[Setup] Setup complete! Running tests...\n');
}

main().catch(error => {
    console.error('[Setup] Unexpected error:', error);
    process.exit(1);
});
