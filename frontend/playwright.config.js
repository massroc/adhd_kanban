import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: 'html',

  // Global setup - ensures test user exists
  globalSetup: './tests/e2e/global-setup.js',

  use: {
    // Base URL for the Tauri app served locally
    baseURL: process.env.TEST_FRONTEND_URL || 'http://localhost:1420',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Serve backend and frontend for testing
  webServer: [
    {
      command: process.platform === 'win32'
        ? '..\\venv\\Scripts\\python manage.py runserver 0.0.0.0:8000'
        : '../venv/bin/python manage.py runserver 0.0.0.0:8000',
      cwd: '../backend',
      url: 'http://localhost:8000/api/v1/health/',
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
    },
    {
      command: 'npx serve src -l 1420 --no-request-logging',
      url: 'http://localhost:1420',
      reuseExistingServer: !process.env.CI,
      timeout: 10000,
    },
  ],
});
